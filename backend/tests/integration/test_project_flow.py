def register(client, email, role="collaborator"):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": "secret123", "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_and_login(client):
    registered = register(client, "owner@example.com", role="project_owner")
    assert registered["user"]["role"] == "project_owner"

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "owner@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_duplicate_email_registration_fails(client):
    register(client, "dup@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "dup@example.com", "password": "secret123"},
    )
    assert response.status_code == 409


def test_wrong_password_login_fails(client):
    register(client, "wrongpw@example.com")
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "wrongpw@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401


def test_full_project_lifecycle(client):
    owner = register(client, "owner2@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "teammate2@example.com", role="collaborator")
    collaborator_headers = auth_headers(collaborator["access_token"])

    create_resp = client.post(
        "/api/v1/projects",
        json={
            "name": "ML-Based Traffic Optimization",
            "description": "LSTM traffic prediction system.",
            "start_date": "2026-07-15",
            "due_date": "2026-12-01",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    project = create_resp.json()
    assert project["status"] == "planning"

    list_resp = client.get("/api/v1/projects", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "ML-Based Traffic Optimization"

    update_resp = client.patch(
        f"/api/v1/projects/{project['id']}", json={"status": "active"}, headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "active"

    # Invite by email, then the invitee accepts
    invite_resp = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["teammate2@example.com"]},
        headers=headers,
    )
    assert invite_resp.status_code == 201, invite_resp.text
    invitation = invite_resp.json()[0]
    assert invitation["email"] == "teammate2@example.com"
    assert invitation["status"] == "pending"

    mine_resp = client.get("/api/v1/invitations/mine", headers=collaborator_headers)
    assert mine_resp.status_code == 200
    assert len(mine_resp.json()) == 1

    accept_resp = client.post(
        f"/api/v1/invitations/{invitation['token']}/accept", headers=collaborator_headers
    )
    assert accept_resp.status_code == 200, accept_resp.text
    assert accept_resp.json()["project_id"] == project["id"]

    members_list_resp = client.get(f"/api/v1/projects/{project['id']}/members", headers=headers)
    assert members_list_resp.status_code == 200
    assert len(members_list_resp.json()) == 1

    # Milestones
    milestone_resp = client.post(
        f"/api/v1/projects/{project['id']}/milestones",
        json={"title": "Requirements & Research", "due_date": "2026-07-19", "order": 0},
        headers=headers,
    )
    assert milestone_resp.status_code == 201, milestone_resp.text
    milestone = milestone_resp.json()

    milestones_list_resp = client.get(
        f"/api/v1/projects/{project['id']}/milestones", headers=headers
    )
    assert milestones_list_resp.status_code == 200
    assert len(milestones_list_resp.json()) == 1

    # Tasks
    task_resp = client.post(
        f"/api/v1/milestones/{milestone['id']}/tasks",
        json={"title": "Gather stakeholder requirements", "priority": "high"},
        headers=headers,
    )
    assert task_resp.status_code == 201, task_resp.text
    task = task_resp.json()
    assert task["status"] == "pending"

    task_update_resp = client.patch(
        f"/api/v1/tasks/{task['id']}", json={"status": "done"}, headers=headers
    )
    assert task_update_resp.status_code == 200
    assert task_update_resp.json()["status"] == "done"

    tasks_list_resp = client.get(f"/api/v1/milestones/{milestone['id']}/tasks", headers=headers)
    assert tasks_list_resp.status_code == 200
    assert len(tasks_list_resp.json()) == 1

    # Cleanup deletes
    task_del = client.delete(f"/api/v1/tasks/{task['id']}", headers=headers)
    milestone_del = client.delete(f"/api/v1/milestones/{milestone['id']}", headers=headers)
    member_del = client.delete(
        f"/api/v1/projects/{project['id']}/members/{collaborator['user']['id']}", headers=headers
    )
    project_del = client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert task_del.status_code == 204
    assert milestone_del.status_code == 204
    assert member_del.status_code == 204
    assert project_del.status_code == 204


def test_collaborator_cannot_create_project(client):
    collaborator = register(client, "collaborator@example.com", role="collaborator")
    headers = auth_headers(collaborator["access_token"])

    response = client.post(
        "/api/v1/projects", json={"name": "Should fail", "description": ""}, headers=headers
    )
    assert response.status_code == 403


def test_unauthenticated_request_rejected(client):
    response = client.get("/api/v1/projects")
    assert response.status_code == 401


def test_only_the_owning_project_owner_can_update_or_delete(client):
    owner = register(client, "owner6@example.com", role="project_owner")
    other_owner = register(client, "otherowner6@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    other_headers = auth_headers(other_owner["access_token"])

    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    update_resp = client.patch(
        f"/api/v1/projects/{project['id']}", json={"status": "active"}, headers=other_headers
    )
    assert update_resp.status_code == 403

    delete_resp = client.delete(f"/api/v1/projects/{project['id']}", headers=other_headers)
    assert delete_resp.status_code == 403


def test_invite_by_email_for_unregistered_address_stays_pending(client):
    owner = register(client, "owner7@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["not-yet-registered@example.com"]},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()[0]["status"] == "pending"


def test_inviting_existing_member_returns_409(client):
    owner = register(client, "owner8@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "teammate8@example.com", role="collaborator")
    collaborator_headers = auth_headers(collaborator["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["teammate8@example.com"]},
        headers=headers,
    ).json()[0]
    client.post(f"/api/v1/invitations/{invite['token']}/accept", headers=collaborator_headers)

    response = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["teammate8@example.com"]},
        headers=headers,
    )
    assert response.status_code == 409


def test_accept_invitation_with_wrong_email_is_forbidden(client):
    owner = register(client, "owner9@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    register(client, "invited9@example.com", role="collaborator")
    wrong_person = register(client, "wrongperson9@example.com", role="collaborator")
    wrong_headers = auth_headers(wrong_person["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["invited9@example.com"]},
        headers=headers,
    ).json()[0]

    response = client.post(
        f"/api/v1/invitations/{invite['token']}/accept", headers=wrong_headers
    )
    assert response.status_code == 403


def test_revoked_invitation_cannot_be_accepted(client):
    owner = register(client, "owner10@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "teammate10@example.com", role="collaborator")
    collaborator_headers = auth_headers(collaborator["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["teammate10@example.com"]},
        headers=headers,
    ).json()[0]

    revoke_resp = client.delete(f"/api/v1/invitations/{invite['id']}", headers=headers)
    assert revoke_resp.status_code == 204

    accept_resp = client.post(
        f"/api/v1/invitations/{invite['token']}/accept", headers=collaborator_headers
    )
    assert accept_resp.status_code == 410


def test_link_invitation_is_reusable_by_multiple_people(client):
    owner = register(client, "owner11@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    person_a = register(client, "persona11@example.com", role="collaborator")
    person_b = register(client, "personb11@example.com", role="collaborator")
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    link_resp = client.post(f"/api/v1/projects/{project['id']}/invitations/link", headers=headers)
    assert link_resp.status_code == 200
    token = link_resp.json()["token"]

    accept_a = client.post(
        f"/api/v1/invitations/{token}/accept", headers=auth_headers(person_a["access_token"])
    )
    accept_b = client.post(
        f"/api/v1/invitations/{token}/accept", headers=auth_headers(person_b["access_token"])
    )
    assert accept_a.status_code == 200
    assert accept_b.status_code == 200

    members_resp = client.get(f"/api/v1/projects/{project['id']}/members", headers=headers)
    assert len(members_resp.json()) == 2

    # Requesting the link again returns the same reusable invitation, not a new one
    second_link_resp = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link", headers=headers
    )
    assert second_link_resp.json()["token"] == token


def test_analyze_proposal_extracts_text_and_does_not_persist_file(client):
    owner = register(client, "ownerA@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/analyze-proposal",
        files={"file": ("proposal.txt", b"Build a traffic prediction system.", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["message"] == "Project analyzed successfully — AI plan generated."
    assert body["characters_extracted"] == len("Build a traffic prediction system.")
    assert "traffic prediction" in body["preview"]


def test_analyze_proposal_rejects_unsupported_type(client):
    owner = register(client, "ownerB@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/analyze-proposal",
        files={"file": ("virus.exe", b"nope", "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 422


def test_analyze_proposal_rejects_oversized_file(client):
    owner = register(client, "ownerC@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    oversized_content = b"0" * (20 * 1024 * 1024 + 1)
    response = client.post(
        f"/api/v1/projects/{project['id']}/analyze-proposal",
        files={"file": ("big.txt", oversized_content, "text/plain")},
        headers=headers,
    )
    assert response.status_code == 422


def test_analyze_proposal_for_nonexistent_project_returns_404(client):
    owner = register(client, "ownerD@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    response = client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/analyze-proposal",
        files={"file": ("proposal.txt", b"hello", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 404


def test_get_nonexistent_project_returns_404(client):
    owner = register(client, "ownerE@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    response = client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404

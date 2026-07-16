def register(client, email, role="member"):
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
    member = register(client, "teammate2@example.com", role="member")

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

    # Team members
    add_member_resp = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "teammate2@example.com"},
        headers=headers,
    )
    assert add_member_resp.status_code == 201, add_member_resp.text
    assert add_member_resp.json()["email"] == "teammate2@example.com"

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
        f"/api/v1/projects/{project['id']}/members/{member['user']['id']}", headers=headers
    )
    project_del = client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert task_del.status_code == 204
    assert milestone_del.status_code == 204
    assert member_del.status_code == 204
    assert project_del.status_code == 204


def test_member_cannot_create_project(client):
    member = register(client, "member@example.com", role="member")
    headers = auth_headers(member["access_token"])

    response = client.post(
        "/api/v1/projects", json={"name": "Should fail", "description": ""}, headers=headers
    )
    assert response.status_code == 403


def test_unauthenticated_request_rejected(client):
    response = client.get("/api/v1/projects")
    assert response.status_code == 401


def test_add_member_with_unknown_email_returns_404(client):
    owner = register(client, "owner6@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "nobody@example.com"},
        headers=headers,
    )
    assert response.status_code == 404


def test_add_duplicate_member_returns_409(client):
    owner = register(client, "owner7@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    register(client, "teammate7@example.com", role="member")
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    first = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "teammate7@example.com"},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"email": "teammate7@example.com"},
        headers=headers,
    )
    assert second.status_code == 409


def test_analyze_proposal_extracts_text_and_does_not_persist_file(client):
    owner = register(client, "owner8@example.com", role="project_owner")
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
    owner = register(client, "owner9@example.com", role="project_owner")
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
    owner = register(client, "owner10@example.com", role="project_owner")
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
    owner = register(client, "owner11@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    response = client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/analyze-proposal",
        files={"file": ("proposal.txt", b"hello", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 404


def test_get_nonexistent_project_returns_404(client):
    owner = register(client, "owner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    response = client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404

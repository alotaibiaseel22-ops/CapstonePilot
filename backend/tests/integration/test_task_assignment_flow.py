def register(client, email, role="collaborator"):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": "secret123", "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_project(client, headers, name="Test Project"):
    return client.post(
        "/api/v1/projects", json={"name": name, "description": ""}, headers=headers
    ).json()


def _guest_join(client, token, display_name="Casey Guest"):
    response = client.post(
        f"/api/v1/invitations/{token}/guest-join", json={"display_name": display_name}
    )
    assert response.status_code == 200, response.text
    return response.json()


def _link_token(client, project_id, headers):
    resp = client.post(f"/api/v1/projects/{project_id}/invitations/link", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["token"]


def _setup_project_with_task(client, owner_headers):
    project = _create_project(client, owner_headers, "Assignment Test Project")
    milestone = client.post(
        f"/api/v1/projects/{project['id']}/milestones",
        json={"title": "Milestone 1", "order": 0},
        headers=owner_headers,
    ).json()
    task = client.post(
        f"/api/v1/milestones/{milestone['id']}/tasks",
        json={"title": "A task"},
        headers=owner_headers,
    ).json()
    return project, task


def test_lists_guests_for_a_project(client):
    owner = register(client, "assignowner1@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    token = _link_token(client, project["id"], headers)
    _guest_join(client, token, display_name="Alex Guest")
    _guest_join(client, token, display_name="Alex Guest")  # second join, same link

    resp = client.get(f"/api/v1/projects/{project['id']}/guests", headers=headers)
    assert resp.status_code == 200
    names = [g["display_name"] for g in resp.json()]
    assert names.count("Alex Guest") == 2  # each join creates its own distinct Guest


def test_assigns_a_task_to_a_real_member(client):
    owner = register(client, "assignowner2@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "assigncollab2@example.com")
    project, task = _setup_project_with_task(client, headers)

    resp = client.patch(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"assignee_id": collaborator["user"]["id"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assignee_id"] == collaborator["user"]["id"]
    assert body["assignee_guest_id"] is None


def test_assigns_a_task_to_a_guest_and_clears_a_prior_member_assignee(client):
    owner = register(client, "assignowner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "assigncollab3@example.com")
    project, task = _setup_project_with_task(client, headers)
    token = _link_token(client, project["id"], headers)
    guest = _guest_join(client, token)["guest"]

    client.patch(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"assignee_id": collaborator["user"]["id"]},
        headers=headers,
    )

    resp = client.patch(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"assignee_guest_id": guest["id"]},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assignee_guest_id"] == guest["id"]
    assert body["assignee_id"] is None  # the prior member assignment was cleared


def test_unassigns_a_task_by_sending_neither_field(client):
    owner = register(client, "assignowner4@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "assigncollab4@example.com")
    project, task = _setup_project_with_task(client, headers)

    client.patch(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"assignee_id": collaborator["user"]["id"]},
        headers=headers,
    )
    resp = client.patch(f"/api/v1/tasks/{task['id']}/assignee", json={}, headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["assignee_id"] is None
    assert body["assignee_guest_id"] is None


def test_assigning_both_a_member_and_a_guest_is_rejected(client):
    owner = register(client, "assignowner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "assigncollab5@example.com")
    project, task = _setup_project_with_task(client, headers)
    token = _link_token(client, project["id"], headers)
    guest = _guest_join(client, token)["guest"]

    resp = client.patch(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"assignee_id": collaborator["user"]["id"], "assignee_guest_id": guest["id"]},
        headers=headers,
    )
    assert resp.status_code == 400


def test_a_guest_cannot_reassign_a_task(client):
    owner = register(client, "assignowner6@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project, task = _setup_project_with_task(client, headers)
    token = _link_token(client, project["id"], headers)
    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    resp = client.patch(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"assignee_guest_id": session["guest"]["id"]},
        headers=guest_headers,
    )
    assert resp.status_code == 403


def test_unassigning_a_guest_revokes_their_status_toggle_capability(client):
    owner = register(client, "assignowner7@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project, task = _setup_project_with_task(client, headers)
    token = _link_token(client, project["id"], headers)
    session = _guest_join(client, token)
    guest = session["guest"]
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    client.patch(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"assignee_guest_id": guest["id"]},
        headers=headers,
    )
    assert (
        client.patch(
            f"/api/v1/tasks/{task['id']}/status", json={"status": "done"}, headers=guest_headers
        ).status_code
        == 200
    )

    client.patch(f"/api/v1/tasks/{task['id']}/assignee", json={}, headers=headers)

    resp = client.patch(
        f"/api/v1/tasks/{task['id']}/status", json={"status": "pending"}, headers=guest_headers
    )
    assert resp.status_code == 403

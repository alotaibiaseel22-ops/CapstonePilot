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

    # Documents
    files = {"file": ("Project_Proposal.pdf", b"%PDF-1.4 fake content", "application/pdf")}
    upload_resp = client.post(
        f"/api/v1/projects/{project['id']}/documents", files=files, headers=headers
    )
    assert upload_resp.status_code == 201, upload_resp.text
    document = upload_resp.json()
    assert document["filename"] == "Project_Proposal.pdf"

    docs_resp = client.get(f"/api/v1/projects/{project['id']}/documents", headers=headers)
    assert docs_resp.status_code == 200
    assert len(docs_resp.json()) == 1

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
    document_del = client.delete(f"/api/v1/documents/{document['id']}", headers=headers)
    project_del = client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert task_del.status_code == 204
    assert milestone_del.status_code == 204
    assert document_del.status_code == 204
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


def test_document_upload_rejects_unsupported_type(client):
    owner = register(client, "owner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/documents",
        files={"file": ("virus.exe", b"nope", "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 422


def test_document_upload_rejects_oversized_file(client):
    owner = register(client, "owner4@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    oversized_content = b"0" * (20 * 1024 * 1024 + 1)
    response = client.post(
        f"/api/v1/projects/{project['id']}/documents",
        files={"file": ("big.txt", oversized_content, "text/plain")},
        headers=headers,
    )
    assert response.status_code == 422


def test_get_nonexistent_project_returns_404(client):
    owner = register(client, "owner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    response = client.get(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404

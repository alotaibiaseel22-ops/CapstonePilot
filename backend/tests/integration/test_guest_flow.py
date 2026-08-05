from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.infrastructure.db.models import InvitationModel


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


def test_guest_join_grants_access_to_its_own_project_but_not_others(client):
    owner = register(client, "guestowner1@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project_a = _create_project(client, headers, "Project A")
    project_b = _create_project(client, headers, "Project B")
    token = _link_token(client, project_a["id"], headers)

    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    own_project = client.get(f"/api/v1/projects/{project_a['id']}", headers=guest_headers)
    assert own_project.status_code == 200
    assert own_project.json()["name"] == "Project A"

    other_project = client.get(f"/api/v1/projects/{project_b['id']}", headers=guest_headers)
    assert other_project.status_code == 403


def test_guest_token_cannot_authenticate_as_a_user(client):
    owner = register(client, "guestowner2@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    token = _link_token(client, project["id"], headers)

    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    # Owner-only / user-only routes must reject a guest token outright, not
    # merely 403 at the route level - decode_access_token rejects it before
    # any route-specific logic runs.
    assert client.get("/api/v1/users/me", headers=guest_headers).status_code == 401
    assert (
        client.post(
            "/api/v1/projects", json={"name": "x", "description": ""}, headers=guest_headers
        ).status_code
        == 401
    )
    assert (
        client.post(
            f"/api/v1/projects/{project['id']}/invitations",
            json={"emails": ["someone@example.com"]},
            headers=guest_headers,
        ).status_code
        == 401
    )


def test_guest_can_view_milestones_and_tasks(client):
    owner = register(client, "guestowner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    milestone = client.post(
        f"/api/v1/projects/{project['id']}/milestones",
        json={"title": "Milestone 1", "order": 0},
        headers=headers,
    ).json()
    client.post(
        f"/api/v1/milestones/{milestone['id']}/tasks",
        json={"title": "Task 1"},
        headers=headers,
    )
    token = _link_token(client, project["id"], headers)
    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    milestones_resp = client.get(
        f"/api/v1/projects/{project['id']}/milestones", headers=guest_headers
    )
    assert milestones_resp.status_code == 200
    assert len(milestones_resp.json()) == 1

    tasks_resp = client.get(f"/api/v1/milestones/{milestone['id']}/tasks", headers=guest_headers)
    assert tasks_resp.status_code == 200
    assert len(tasks_resp.json()) == 1


def test_guest_can_only_update_status_of_their_own_assigned_task(client):
    owner = register(client, "guestowner4@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    milestone = client.post(
        f"/api/v1/projects/{project['id']}/milestones",
        json={"title": "Milestone 1", "order": 0},
        headers=headers,
    ).json()
    token = _link_token(client, project["id"], headers)
    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}
    guest_id = session["guest"]["id"]

    my_task = client.post(
        f"/api/v1/milestones/{milestone['id']}/tasks",
        json={"title": "My task", "assignee_guest_id": guest_id},
        headers=headers,
    ).json()
    other_task = client.post(
        f"/api/v1/milestones/{milestone['id']}/tasks",
        json={"title": "Someone else's task"},
        headers=headers,
    ).json()

    mine_resp = client.patch(
        f"/api/v1/tasks/{my_task['id']}/status", json={"status": "done"}, headers=guest_headers
    )
    assert mine_resp.status_code == 200
    assert mine_resp.json()["status"] == "done"

    others_resp = client.patch(
        f"/api/v1/tasks/{other_task['id']}/status",
        json={"status": "done"},
        headers=guest_headers,
    )
    assert others_resp.status_code == 403

    # A guest can never reach the full update route at all - it stays
    # get_current_user-only, so a guest token is rejected outright.
    full_update_resp = client.patch(
        f"/api/v1/tasks/{my_task['id']}", json={"title": "hijacked"}, headers=guest_headers
    )
    assert full_update_resp.status_code == 401


def test_guest_session_resume_does_not_create_a_new_guest(client):
    owner = register(client, "guestowner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    token = _link_token(client, project["id"], headers)

    first = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {first['guest_access_token']}"}

    resumed = client.get(f"/api/v1/invitations/{token}/guest-session", headers=guest_headers)
    assert resumed.status_code == 200
    assert resumed.json()["guest"]["id"] == first["guest"]["id"]


def test_revoking_invitation_invalidates_already_issued_guest_token(client):
    owner = register(client, "guestowner6@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    invitation = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link", headers=headers
    ).json()
    token = invitation["token"]

    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}
    assert client.get(f"/api/v1/projects/{project['id']}", headers=guest_headers).status_code == 200

    revoke_resp = client.delete(f"/api/v1/invitations/{invitation['id']}", headers=headers)
    assert revoke_resp.status_code == 204

    # The already-issued token is still cryptographically valid but must now
    # be rejected - resolve_guest re-checks the invitation's live status.
    after_revoke = client.get(f"/api/v1/projects/{project['id']}", headers=guest_headers)
    assert after_revoke.status_code == 403 or after_revoke.status_code == 401


def test_expired_link_invitation_blocks_new_guest_join(client):
    owner = register(client, "guestowner7@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    invitation = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link", headers=headers
    ).json()

    db = client.session_factory()
    try:
        model = (
            db.query(InvitationModel).filter(InvitationModel.id == UUID(invitation["id"])).first()
        )
        model.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/api/v1/invitations/{invitation['token']}/guest-join",
        json={"display_name": "Too Late"},
    )
    assert response.status_code == 410


def test_email_invitation_cannot_be_used_for_guest_join(client):
    owner = register(client, "guestowner8@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["invitee@example.com"]},
        headers=headers,
    ).json()[0]

    response = client.post(
        f"/api/v1/invitations/{invite['token']}/guest-join",
        json={"display_name": "Sneaky"},
    )
    assert response.status_code == 400

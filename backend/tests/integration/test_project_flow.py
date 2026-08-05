from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.api.v1.deps import get_session_factory
from app.infrastructure.db.models import InvitationModel
from app.main import app


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


def test_cors_allows_any_localhost_dev_port_but_not_other_origins(client):
    # Vite auto-bumps to another port (5174, 5175, ...) the moment 5173 is
    # already taken by a leftover process - without allow_origin_regex in
    # development, that silent port change makes the frontend's API calls
    # fail as an opaque network error indistinguishable from the backend
    # being down, since a CORS rejection never reaches application code.
    configured_origin = client.options(
        "/api/v1/auth/register",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert configured_origin.status_code == 200

    other_dev_port = client.options(
        "/api/v1/auth/register",
        headers={"Origin": "http://localhost:5174", "Access-Control-Request-Method": "POST"},
    )
    assert other_dev_port.status_code == 200

    untrusted_origin = client.options(
        "/api/v1/auth/register",
        headers={"Origin": "http://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert untrusted_origin.status_code == 400


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


def test_registration_rejects_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Short Pw", "email": "shortpw@example.com", "password": "abc"},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item["loc"] == ["body", "password"] for item in detail)


def test_registration_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Bad Email", "email": "not-an-email", "password": "secret123"},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(item["loc"] == ["body", "email"] for item in detail)


def test_successful_registration_persists_a_real_user_row(client):
    from uuid import UUID

    from app.infrastructure.db.models import UserModel

    registered = register(client, "persisted@example.com", role="project_owner")
    user_id = UUID(registered["user"]["id"])

    db = client.session_factory()
    try:
        model = db.get(UserModel, user_id)
        assert model is not None
        assert model.email == "persisted@example.com"
        assert model.password_hash != "secret123"
    finally:
        db.close()


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


def test_list_projects_only_returns_projects_you_own_or_belong_to(client):
    owner = register(client, "listowner@example.com", role="project_owner")
    member = register(client, "listmember@example.com", role="collaborator")
    stranger = register(client, "liststranger@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    member_headers = auth_headers(member["access_token"])
    stranger_headers = auth_headers(stranger["access_token"])

    owned_project = client.post(
        "/api/v1/projects", json={"name": "Owner's Project", "description": ""}, headers=headers
    ).json()
    # A second project owned by the same "stranger" role user, unrelated to
    # the other two - proves list_projects doesn't just return everything.
    client.post(
        "/api/v1/projects", json={"name": "Stranger's Project", "description": ""},
        headers=stranger_headers,
    )

    invite = client.post(
        f"/api/v1/projects/{owned_project['id']}/invitations",
        json={"emails": ["listmember@example.com"]},
        headers=headers,
    ).json()[0]
    client.post(f"/api/v1/invitations/{invite['token']}/accept", headers=member_headers)

    owner_list = client.get("/api/v1/projects", headers=headers).json()
    assert [p["id"] for p in owner_list] == [owned_project["id"]]

    member_list = client.get("/api/v1/projects", headers=member_headers).json()
    assert [p["id"] for p in member_list] == [owned_project["id"]]

    stranger_list = client.get("/api/v1/projects", headers=stranger_headers).json()
    assert owned_project["id"] not in [p["id"] for p in stranger_list]


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


def test_plan_generate_accepts_a_proposal_and_returns_a_job_id(client):
    app.dependency_overrides[get_session_factory] = lambda: client.session_factory
    owner = register(client, "ownerA@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/plan/generate",
        files={"file": ("proposal.txt", b"Build a traffic prediction system.", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 202, response.text
    assert "job_id" in response.json()


def test_plan_generate_rejects_unsupported_type(client):
    owner = register(client, "ownerB@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/plan/generate",
        files={"file": ("virus.exe", b"nope", "application/octet-stream")},
        headers=headers,
    )
    assert response.status_code == 422


def test_plan_generate_rejects_oversized_file(client):
    owner = register(client, "ownerC@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    oversized_content = b"0" * (20 * 1024 * 1024 + 1)
    response = client.post(
        f"/api/v1/projects/{project['id']}/plan/generate",
        files={"file": ("big.txt", oversized_content, "text/plain")},
        headers=headers,
    )
    assert response.status_code == 422


def test_plan_generate_for_nonexistent_project_returns_404(client):
    owner = register(client, "ownerD@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    response = client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/plan/generate",
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


def test_project_read_includes_owner_name_and_email(client):
    owner = register(client, "ownerF@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()
    assert project["owner_name"] == "Test User"
    assert project["owner_email"] == "ownerF@example.com"


def test_resend_invitation_refreshes_expiry_and_requires_owner(client):
    owner = register(client, "owner12@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    outsider = register(client, "outsider12@example.com", role="project_owner")
    outsider_headers = auth_headers(outsider["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["teammate12@example.com"]},
        headers=headers,
    ).json()[0]

    forbidden = client.post(
        f"/api/v1/invitations/{invite['id']}/resend", headers=outsider_headers
    )
    assert forbidden.status_code == 403

    resent = client.post(f"/api/v1/invitations/{invite['id']}/resend", headers=headers)
    assert resent.status_code == 200
    assert resent.json()["token"] == invite["token"]
    assert resent.json()["expires_at"] > invite["expires_at"]


def test_resend_link_invitation_is_rejected(client):
    owner = register(client, "owner13@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    link = client.post(f"/api/v1/projects/{project['id']}/invitations/link", headers=headers).json()

    response = client.post(f"/api/v1/invitations/{link['id']}/resend", headers=headers)
    assert response.status_code == 400


def test_preview_invitation_reports_project_and_account_status(client):
    owner = register(client, "owner14@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    register(client, "known14@example.com", role="collaborator")
    project = client.post(
        "/api/v1/projects", json={"name": "Preview Project", "description": ""}, headers=headers
    ).json()

    known_invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["known14@example.com"]},
        headers=headers,
    ).json()[0]
    unknown_invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["unknown14@example.com"]},
        headers=headers,
    ).json()[0]

    known_preview = client.get(f"/api/v1/invitations/{known_invite['token']}/preview")
    assert known_preview.status_code == 200
    assert known_preview.json() == {
        "project_name": "Preview Project",
        "inviter_name": "Test User",
        "email": "known14@example.com",
        "user_exists": True,
        "is_valid": True,
    }

    unknown_preview = client.get(f"/api/v1/invitations/{unknown_invite['token']}/preview")
    assert unknown_preview.json()["user_exists"] is False

    missing = client.get("/api/v1/invitations/not-a-real-token/preview")
    assert missing.status_code == 404


def test_expired_email_invitation_cannot_be_accepted(client):
    owner = register(client, "owner15@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "teammate15@example.com", role="collaborator")
    collaborator_headers = auth_headers(collaborator["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["teammate15@example.com"]},
        headers=headers,
    ).json()[0]

    db = client.session_factory()
    try:
        model = (
            db.query(InvitationModel).filter(InvitationModel.id == UUID(invite["id"])).first()
        )
        model.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/api/v1/invitations/{invite['token']}/accept", headers=collaborator_headers
    )
    assert response.status_code == 410


def test_onboarding_via_invitation_creates_a_participant_and_returns_a_session(client):
    owner = register(client, "owner17@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Onboard Project", "description": ""}, headers=headers
    ).json()
    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["newcomer17@example.com"]},
        headers=headers,
    ).json()[0]

    response = client.post(
        f"/api/v1/invitations/{invite['token']}/onboard", json={"name": "Newcomer Nadia"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["user"]["name"] == "Newcomer Nadia"
    assert body["user"]["email"] == "newcomer17@example.com"
    assert body["user"]["role"] == "collaborator"

    # The returned token really is a usable session - not just a shaped response.
    me = client.get("/api/v1/users/me", headers=auth_headers(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "newcomer17@example.com"

    members = client.get(f"/api/v1/projects/{project['id']}/members", headers=headers).json()
    assert any(m["email"] == "newcomer17@example.com" for m in members)


def test_onboarding_is_rejected_when_the_email_already_has_an_account(client):
    owner = register(client, "owner18@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    register(client, "existing18@example.com", role="collaborator")
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()
    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["existing18@example.com"]},
        headers=headers,
    ).json()[0]

    response = client.post(
        f"/api/v1/invitations/{invite['token']}/onboard", json={"name": "Someone"}
    )
    assert response.status_code == 409


def test_onboarding_is_rejected_for_a_shareable_link_invitation(client):
    owner = register(client, "owner19@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()
    link_invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link", headers=headers
    ).json()

    response = client.post(
        f"/api/v1/invitations/{link_invite['token']}/onboard", json={"name": "Someone"}
    )
    assert response.status_code == 400


def test_onboarding_twice_with_the_same_token_is_rejected(client):
    owner = register(client, "owner20@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()
    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["newcomer20@example.com"]},
        headers=headers,
    ).json()[0]

    first = client.post(
        f"/api/v1/invitations/{invite['token']}/onboard", json={"name": "First Try"}
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/invitations/{invite['token']}/onboard", json={"name": "Second Try"}
    )
    assert second.status_code == 409


def test_owner_cannot_be_removed_and_removal_requires_ownership(client):
    owner = register(client, "owner16@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    outsider = register(client, "outsider16@example.com", role="project_owner")
    outsider_headers = auth_headers(outsider["access_token"])
    collaborator = register(client, "teammate16@example.com", role="collaborator")
    collaborator_headers = auth_headers(collaborator["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["teammate16@example.com"]},
        headers=headers,
    ).json()[0]
    client.post(f"/api/v1/invitations/{invite['token']}/accept", headers=collaborator_headers)

    owner_id = owner["user"]["id"]
    collaborator_id = collaborator["user"]["id"]

    cannot_remove_owner = client.delete(
        f"/api/v1/projects/{project['id']}/members/{owner_id}", headers=headers
    )
    assert cannot_remove_owner.status_code == 400

    forbidden = client.delete(
        f"/api/v1/projects/{project['id']}/members/{collaborator_id}", headers=outsider_headers
    )
    assert forbidden.status_code == 403

    allowed = client.delete(
        f"/api/v1/projects/{project['id']}/members/{collaborator_id}", headers=headers
    )
    assert allowed.status_code == 204


def test_delete_project_cascades_members_and_invitations(client):
    owner = register(client, "owner17@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    collaborator = register(client, "teammate17@example.com", role="collaborator")
    collaborator_headers = auth_headers(collaborator["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    invite = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["teammate17@example.com"]},
        headers=headers,
    ).json()[0]
    client.post(f"/api/v1/invitations/{invite['token']}/accept", headers=collaborator_headers)
    client.post(
        f"/api/v1/projects/{project['id']}/milestones",
        json={"title": "Kickoff", "order": 0},
        headers=headers,
    )

    delete_resp = client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert delete_resp.status_code == 204

    db = client.session_factory()
    try:
        from app.infrastructure.db.models import MilestoneModel, PlanModel, ProjectMemberModel

        project_id = UUID(project["id"])
        assert db.query(ProjectMemberModel).filter_by(project_id=project_id).count() == 0
        assert db.query(InvitationModel).filter_by(project_id=project_id).count() == 0
        assert db.query(PlanModel).filter_by(project_id=project_id).count() == 0
        assert db.query(MilestoneModel).count() == 0
    finally:
        db.close()


def test_deleting_a_project_with_an_agent_run_succeeds(client):
    """Regression test for a real production bug: deleting a project 500'd
    with a foreign key IntegrityError because agent_runs.project_id was
    never included in delete_project()'s cascade, even though every plan
    generation and risk-analysis tick creates an AgentRun row tied to the
    project. Inserts one directly (rather than driving a full plan
    generation) since the point is specifically that this row exists and
    must not block deletion, not how it got there."""
    owner = register(client, "owner17b@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Agent Run Cascade Project", "description": ""},
        headers=headers,
    ).json()
    project_id = UUID(project["id"])

    db = client.session_factory()
    try:
        from app.infrastructure.db.models import AgentRunModel

        now = datetime.now(UTC)
        db.add(
            AgentRunModel(
                id=uuid4(),
                project_id=project_id,
                agent_type="planner",
                status="succeeded",
                input_ref={},
                output_ref={"summary": "test"},
                error=None,
                created_at=now,
                updated_at=now,
            )
        )
        db.commit()
        assert db.query(AgentRunModel).filter_by(project_id=project_id).count() == 1
    finally:
        db.close()

    delete_resp = client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert delete_resp.status_code == 204, delete_resp.text

    db = client.session_factory()
    try:
        from app.infrastructure.db.models import AgentRunModel

        assert db.query(AgentRunModel).filter_by(project_id=project_id).count() == 0
    finally:
        db.close()


def test_regenerate_link_invitation_revokes_old_token_and_requires_ownership(client):
    owner = register(client, "owner18@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    outsider = register(client, "outsider18@example.com", role="project_owner")
    outsider_headers = auth_headers(outsider["access_token"])
    person = register(client, "person18@example.com", role="collaborator")
    person_headers = auth_headers(person["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Test Project", "description": ""}, headers=headers
    ).json()

    first_link = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link", headers=headers
    ).json()

    forbidden = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link/regenerate", headers=outsider_headers
    )
    assert forbidden.status_code == 403

    second_link = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link/regenerate", headers=headers
    ).json()
    assert second_link["token"] != first_link["token"]

    old_token_accept = client.post(
        f"/api/v1/invitations/{first_link['token']}/accept", headers=person_headers
    )
    assert old_token_accept.status_code == 410

    new_token_accept = client.post(
        f"/api/v1/invitations/{second_link['token']}/accept", headers=person_headers
    )
    assert new_token_accept.status_code == 200

    # Regenerating again after the old link was already revoked shouldn't error
    third_link = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link/regenerate", headers=headers
    ).json()
    assert third_link["token"] != second_link["token"]

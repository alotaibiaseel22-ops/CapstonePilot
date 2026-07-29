def register(client, email, role="collaborator"):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": "secret123", "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_updating_the_profile_name_persists_and_is_reflected_in_me(client):
    owner = register(client, "settings-owner1@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    resp = client.patch("/api/v1/users/me", json={"name": "New Name"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "New Name"

    me = client.get("/api/v1/users/me", headers=headers)
    assert me.json()["name"] == "New Name"


def test_updating_the_language_preference_persists(client):
    owner = register(client, "settings-owner2@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    resp = client.patch("/api/v1/users/me", json={"preferred_language": "ar"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["preferred_language"] == "ar"


def test_changing_the_password_allows_login_with_the_new_one(client):
    owner = register(client, "settings-owner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    resp = client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "secret123", "new_password": "newsecret456"},
        headers=headers,
    )
    assert resp.status_code == 204, resp.text

    old_login = client.post(
        "/api/v1/auth/login",
        data={"username": "settings-owner3@example.com", "password": "secret123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        data={"username": "settings-owner3@example.com", "password": "newsecret456"},
    )
    assert new_login.status_code == 200


def test_changing_the_password_with_the_wrong_current_password_fails(client):
    owner = register(client, "settings-owner4@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    resp = client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "wrongpassword", "new_password": "newsecret456"},
        headers=headers,
    )
    assert resp.status_code == 400

    # The old password must still work - nothing should have changed.
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "settings-owner4@example.com", "password": "secret123"},
    )
    assert login.status_code == 200


def test_profile_and_password_endpoints_require_auth(client):
    resp = client.patch("/api/v1/users/me", json={"name": "X"})
    assert resp.status_code == 401

    resp = client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "a", "new_password": "newsecret456"},
    )
    assert resp.status_code == 401

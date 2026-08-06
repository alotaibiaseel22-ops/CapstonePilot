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


def _post_comment(client, project_id, body, headers=None):
    return client.post(
        f"/api/v1/projects/{project_id}/comments", json={"body": body}, headers=headers
    )


def test_owner_posts_and_lists_a_comment(client):
    owner = register(client, "commentowner1@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)

    resp = _post_comment(client, project["id"], "First comment", headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["body"] == "First comment"
    assert body["author_id"] == owner["user"]["id"]
    assert body["author_guest_id"] is None

    listed = client.get(f"/api/v1/projects/{project['id']}/comments", headers=headers).json()
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]


def test_guest_posts_a_comment(client):
    owner = register(client, "commentowner2@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    token = _link_token(client, project["id"], headers)
    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    resp = _post_comment(client, project["id"], "Hello from a guest", guest_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["author_guest_id"] == session["guest"]["id"]
    assert body["author_id"] is None


def test_comments_are_listed_oldest_first(client):
    owner = register(client, "commentowner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)

    _post_comment(client, project["id"], "first", headers)
    _post_comment(client, project["id"], "second", headers)
    _post_comment(client, project["id"], "third", headers)

    listed = client.get(f"/api/v1/projects/{project['id']}/comments", headers=headers).json()
    assert [c["body"] for c in listed] == ["first", "second", "third"]


def test_empty_comment_is_rejected(client):
    owner = register(client, "commentowner4@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)

    resp = _post_comment(client, project["id"], "   ", headers)
    assert resp.status_code == 422


def test_a_guest_bound_to_one_project_cannot_touch_another_projects_comments(client):
    owner = register(client, "commentowner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project_a = _create_project(client, headers, "Project A")
    project_b = _create_project(client, headers, "Project B")
    token_a = _link_token(client, project_a["id"], headers)
    session = _guest_join(client, token_a)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    _post_comment(client, project_b["id"], "owner's comment", headers)

    resp = client.get(f"/api/v1/projects/{project_b['id']}/comments", headers=guest_headers)
    assert resp.status_code == 403


def test_non_author_non_owner_member_cannot_delete_but_author_and_owner_can(client):
    owner = register(client, "commentowner6@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    other_member = register(client, "commentother6@example.com")
    project = _create_project(client, headers)
    token = _link_token(client, project["id"], headers)
    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    invites = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["commentother6@example.com"]},
        headers=headers,
    ).json()
    client.post(
        f"/api/v1/invitations/{invites[0]['token']}/accept",
        headers=auth_headers(other_member["access_token"]),
    )

    posted = _post_comment(client, project["id"], "guest's comment", guest_headers).json()

    other_headers = auth_headers(other_member["access_token"])
    forbidden = client.delete(
        f"/api/v1/projects/{project['id']}/comments/{posted['id']}", headers=other_headers
    )
    assert forbidden.status_code == 403

    owner_delete = client.delete(
        f"/api/v1/projects/{project['id']}/comments/{posted['id']}", headers=headers
    )
    assert owner_delete.status_code == 204

    second = _post_comment(client, project["id"], "another one", guest_headers).json()
    author_delete = client.delete(
        f"/api/v1/projects/{project['id']}/comments/{second['id']}", headers=guest_headers
    )
    assert author_delete.status_code == 204

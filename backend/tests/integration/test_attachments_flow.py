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


def _upload(client, project_id, headers=None, filename="notes.txt", content=b"hello world"):
    return client.post(
        f"/api/v1/projects/{project_id}/attachments",
        files={"file": (filename, content, "text/plain")},
        headers=headers,
    )


def test_owner_uploads_and_lists_an_attachment(client):
    owner = register(client, "attachowner1@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)

    resp = _upload(client, project["id"], headers, content=b"the file contents")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["filename"] == "notes.txt"
    assert body["content_type"] == "text/plain"
    assert body["size_bytes"] == len(b"the file contents")
    assert body["uploader_id"] == owner["user"]["id"]
    assert body["uploader_guest_id"] is None
    assert "content" not in body

    listed = client.get(f"/api/v1/projects/{project['id']}/attachments", headers=headers).json()
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]
    assert "content" not in listed[0]


def test_guest_uploads_an_attachment(client):
    owner = register(client, "attachowner2@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    token = _link_token(client, project["id"], headers)
    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    resp = _upload(client, project["id"], guest_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["uploader_guest_id"] == session["guest"]["id"]
    assert body["uploader_id"] is None


def test_download_returns_exact_bytes_and_headers(client):
    owner = register(client, "attachowner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)
    original = b"\x00binary-ish content \xff with weird bytes"

    uploaded = _upload(client, project["id"], headers, filename="data.bin", content=original).json()

    resp = client.get(
        f"/api/v1/projects/{project['id']}/attachments/{uploaded['id']}/download",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.content == original
    assert "data.bin" in resp.headers["content-disposition"]


def test_a_guest_bound_to_one_project_cannot_touch_another_projects_attachments(client):
    owner = register(client, "attachowner4@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project_a = _create_project(client, headers, "Project A")
    project_b = _create_project(client, headers, "Project B")
    token_a = _link_token(client, project_a["id"], headers)
    session = _guest_join(client, token_a)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    uploaded = _upload(client, project_b["id"], headers).json()

    list_resp = client.get(
        f"/api/v1/projects/{project_b['id']}/attachments", headers=guest_headers
    )
    assert list_resp.status_code == 403
    assert (
        client.get(
            f"/api/v1/projects/{project_b['id']}/attachments/{uploaded['id']}/download",
            headers=guest_headers,
        ).status_code
        == 403
    )


def test_non_author_non_owner_member_cannot_delete_but_author_and_owner_can(client):
    owner = register(client, "attachowner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    other_member = register(client, "attachother5@example.com")
    project = _create_project(client, headers)
    token = _link_token(client, project["id"], headers)
    session = _guest_join(client, token)
    guest_headers = {"Authorization": f"Bearer {session['guest_access_token']}"}

    # Make other_member a real project member via the accept flow.
    invites = client.post(
        f"/api/v1/projects/{project['id']}/invitations",
        json={"emails": ["attachother5@example.com"]},
        headers=headers,
    ).json()
    client.post(
        f"/api/v1/invitations/{invites[0]['token']}/accept",
        headers=auth_headers(other_member["access_token"]),
    )

    uploaded = _upload(client, project["id"], guest_headers).json()

    other_headers = auth_headers(other_member["access_token"])
    forbidden = client.delete(
        f"/api/v1/projects/{project['id']}/attachments/{uploaded['id']}", headers=other_headers
    )
    assert forbidden.status_code == 403

    owner_delete = client.delete(
        f"/api/v1/projects/{project['id']}/attachments/{uploaded['id']}", headers=headers
    )
    assert owner_delete.status_code == 204

    second = _upload(client, project["id"], guest_headers).json()
    author_delete = client.delete(
        f"/api/v1/projects/{project['id']}/attachments/{second['id']}", headers=guest_headers
    )
    assert author_delete.status_code == 204


def test_upload_over_size_limit_is_rejected(client):
    owner = register(client, "attachowner6@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_project(client, headers)

    too_big = b"x" * (20 * 1024 * 1024 + 1)
    resp = _upload(client, project["id"], headers, content=too_big)
    assert resp.status_code == 422

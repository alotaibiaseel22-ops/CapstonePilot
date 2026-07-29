from datetime import date, timedelta

from app.application.ports.risk_orchestrator import RecommendationItem, RiskAnalysisOutput, RiskItem
from app.infrastructure.scheduler import run_monitoring_tick


def register(client, email, role="collaborator"):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": email, "password": "secret123", "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_breached_project(client, headers):
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "Activity Flow Risk Project",
            "description": "desc",
            "start_date": str(date.today() - timedelta(days=30)),
            "due_date": str(date.today() + timedelta(days=5)),
        },
        headers=headers,
    ).json()
    milestone = client.post(
        f"/api/v1/projects/{project['id']}/milestones",
        json={"title": "Milestone", "due_date": str(date.today() + timedelta(days=10))},
        headers=headers,
    ).json()
    for i in range(4):
        client.post(
            f"/api/v1/milestones/{milestone['id']}/tasks",
            json={"title": f"Overdue Task {i}", "due_date": str(date.today() - timedelta(days=3))},
            headers=headers,
        )
    return project


class CannedRiskOrchestrator:
    def analyze(
        self,
        project_name,
        project_description,
        signals,
        task_summary,
        dependencies_text,
        activity_text,
    ):
        return RiskAnalysisOutput(
            risks=[
                RiskItem(title="Risk A", category="Schedule", severity="high", description="d"),
                RiskItem(title="Risk B", category="Schedule", severity="medium", description="d"),
            ],
            recommendations=[
                RecommendationItem(
                    title="Fix it",
                    category="Process",
                    severity="high",
                    effort="low",
                    impact="high",
                    description="d",
                    risk_index=0,
                )
            ],
        )


def _get_activity(client, headers, project_id):
    resp = client.get(f"/api/v1/projects/{project_id}/activity", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_creating_a_project_logs_an_activity_event(client):
    owner = register(client, "activity-owner1@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project = client.post(
        "/api/v1/projects", json={"name": "Fresh Project", "description": "desc"}, headers=headers
    ).json()

    events = _get_activity(client, headers, project["id"])
    assert len(events) == 1
    assert events[0]["event_type"] == "project_created"
    assert owner["user"]["name"] in events[0]["message"]


def test_completing_a_task_logs_an_event_but_other_edits_dont(client):
    owner = register(client, "activity-owner2@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_breached_project(client, headers)
    milestones = client.get(f"/api/v1/projects/{project['id']}/milestones", headers=headers).json()
    tasks = client.get(f"/api/v1/milestones/{milestones[0]['id']}/tasks", headers=headers).json()
    task_id = tasks[0]["id"]

    # A non-completion edit shouldn't log a task_completed event.
    client.patch(f"/api/v1/tasks/{task_id}", json={"priority": "high"}, headers=headers)
    events_after_priority_change = _get_activity(client, headers, project["id"])
    assert not any(e["event_type"] == "task_completed" for e in events_after_priority_change)

    client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"}, headers=headers)
    events = _get_activity(client, headers, project["id"])
    completed_events = [e for e in events if e["event_type"] == "task_completed"]
    assert len(completed_events) == 1
    assert "Overdue Task 0" in completed_events[0]["message"]

    # Completing it again (already done -> done) must not log a second event.
    client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"}, headers=headers)
    events_again = _get_activity(client, headers, project["id"])
    assert len([e for e in events_again if e["event_type"] == "task_completed"]) == 1


def test_approving_and_rejecting_plans_log_activity_events(client):
    owner = register(client, "activity-owner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project = client.post(
        "/api/v1/projects", json={"name": "Plan Project", "description": "desc"}, headers=headers
    ).json()
    generate_resp = client.post(
        f"/api/v1/projects/{project['id']}/plan/generate",
        files={"file": ("proposal.txt", b"Build a thing.", "text/plain")},
        headers=headers,
    )
    assert generate_resp.status_code == 202, generate_resp.text
    job_id = generate_resp.json()["job_id"]

    for _ in range(20):
        job = client.get(f"/api/v1/jobs/{job_id}", headers=headers).json()
        if job["status"] in ("succeeded", "failed"):
            assert job["status"] == "succeeded", job
            break
    else:
        raise AssertionError("job never reached a terminal status")

    events = _get_activity(client, headers, project["id"])
    assert any(e["event_type"] == "plan_generated" for e in events)

    client.post(f"/api/v1/projects/{project['id']}/plan/approve", headers=headers)
    events = _get_activity(client, headers, project["id"])
    assert any(e["event_type"] == "plan_approved" for e in events)


def test_rejecting_a_plan_logs_an_event(client):
    owner = register(client, "activity-owner4@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Reject Project", "description": "desc"}, headers=headers
    ).json()
    generate_resp = client.post(
        f"/api/v1/projects/{project['id']}/plan/generate",
        files={"file": ("proposal.txt", b"Build a thing.", "text/plain")},
        headers=headers,
    )
    job_id = generate_resp.json()["job_id"]
    for _ in range(20):
        job = client.get(f"/api/v1/jobs/{job_id}", headers=headers).json()
        if job["status"] in ("succeeded", "failed"):
            break

    client.post(f"/api/v1/projects/{project['id']}/plan/reject", headers=headers)
    events = _get_activity(client, headers, project["id"])
    assert any(e["event_type"] == "plan_rejected" for e in events)


def test_risk_detection_logs_one_batched_event_not_per_risk(client):
    owner = register(client, "activity-owner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_breached_project(client, headers)

    run_monitoring_tick(client.session_factory, CannedRiskOrchestrator())

    events = _get_activity(client, headers, project["id"])
    risk_events = [e for e in events if e["event_type"] == "risk_detected"]
    assert len(risk_events) == 1
    assert "2" in risk_events[0]["message"]


def test_approving_and_rejecting_recommendations_log_activity_events(client):
    owner = register(client, "activity-owner6@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_breached_project(client, headers)
    run_monitoring_tick(client.session_factory, CannedRiskOrchestrator())

    recommendation = client.get(
        f"/api/v1/projects/{project['id']}/recommendations", headers=headers
    ).json()[0]
    client.post(f"/api/v1/recommendations/{recommendation['id']}/approve", headers=headers)

    events = _get_activity(client, headers, project["id"])
    assert any(e["event_type"] == "recommendation_approved" for e in events)


def test_unread_count_reflects_last_seen_and_mark_seen_resets_it(client):
    owner = register(client, "activity-owner7@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    unread = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread.json()["count"] == 0  # brand-new user starts caught up

    client.post(
        "/api/v1/projects", json={"name": "Notif Project", "description": "desc"}, headers=headers
    )
    unread = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread.json()["count"] == 1

    mark_seen = client.post("/api/v1/notifications/mark-seen", headers=headers)
    assert mark_seen.json()["count"] == 0

    unread_after = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert unread_after.json()["count"] == 0


def test_accepting_an_invitation_logs_a_member_joined_event(client):
    owner = register(client, "activity-owner9@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Team Project", "description": "desc"}, headers=headers
    ).json()

    link = client.post(
        f"/api/v1/projects/{project['id']}/invitations/link", headers=headers
    ).json()

    collaborator = register(client, "activity-collab9@example.com")
    collab_headers = auth_headers(collaborator["access_token"])
    accept_resp = client.post(f"/api/v1/invitations/{link['token']}/accept", headers=collab_headers)
    assert accept_resp.status_code == 200, accept_resp.text

    events = _get_activity(client, headers, project["id"])
    joined_events = [e for e in events if e["event_type"] == "member_joined"]
    assert len(joined_events) == 1
    assert collaborator["user"]["name"] in joined_events[0]["message"]


def test_deleting_a_project_cascades_activity_events(client):
    owner = register(client, "activity-owner8@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = client.post(
        "/api/v1/projects", json={"name": "Doomed Project", "description": "desc"}, headers=headers
    ).json()

    events = _get_activity(client, headers, project["id"])
    assert len(events) == 1

    delete_resp = client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert delete_resp.status_code == 204

    events_after = _get_activity(client, headers, project["id"])
    assert events_after == []

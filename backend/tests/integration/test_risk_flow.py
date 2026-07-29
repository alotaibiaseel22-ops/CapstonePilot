import uuid
from datetime import date, timedelta

from app.api.v1.deps import get_risk_orchestrator
from app.application.ports.risk_orchestrator import RecommendationItem, RiskAnalysisOutput, RiskItem
from app.core.config import settings
from app.infrastructure.agents.fake_risk_orchestrator import FakeRiskOrchestrator
from app.infrastructure.db.models import AgentRunModel
from app.infrastructure.scheduler import run_monitoring_tick
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


class CannedRiskOrchestrator:
    """Deterministic stand-in for the real CrewAI orchestrator - proves the
    scheduler's persistence plumbing works without any network/LLM call.
    Caching is entirely the scheduler's responsibility (run_monitoring_tick
    checks risk_cache before ever calling analyze()), so this double doesn't
    need to know about it - a cache-hit tick is proven to make zero extra
    calls because the scheduler never reaches this method at all."""

    def __init__(self):
        self.call_count = 0

    def analyze(
        self,
        project_name,
        project_description,
        signals,
        task_summary,
        dependencies_text,
        activity_text,
    ):
        self.call_count += 1
        assert task_summary  # the task titles really were passed through
        return RiskAnalysisOutput(
            risks=[
                RiskItem(
                    title="Backend tasks slipping",
                    category="Schedule",
                    severity="high",
                    description="Several backend tasks are overdue.",
                )
            ],
            recommendations=[
                RecommendationItem(
                    title="Redistribute overdue backend tasks",
                    category="Team",
                    severity="high",
                    effort="low",
                    impact="high",
                    description="Move overdue tasks to a teammate with capacity.",
                    rationale="Reduces bottleneck risk.",
                    risk_index=0,
                )
            ],
        )


def _create_breached_project(client, headers):
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "Risk Flow Project",
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


def test_monitoring_tick_creates_risks_and_recommendations_for_a_breached_project(client):
    owner = register(client, "risk-owner1@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_breached_project(client, headers)

    orchestrator = CannedRiskOrchestrator()
    run_monitoring_tick(client.session_factory, orchestrator)
    assert orchestrator.call_count == 1

    risks_resp = client.get(f"/api/v1/projects/{project['id']}/risks", headers=headers)
    assert risks_resp.status_code == 200
    risks = risks_resp.json()
    assert len(risks) == 1
    assert risks[0]["title"] == "Backend tasks slipping"
    assert risks[0]["severity"] == "high"

    recs_resp = client.get(f"/api/v1/projects/{project['id']}/recommendations", headers=headers)
    recs = recs_resp.json()
    assert len(recs) == 1
    assert recs[0]["title"] == "Redistribute overdue backend tasks"
    assert recs[0]["status"] == "pending"
    assert recs[0]["risk_report_id"] == risks[0]["id"]

    db = client.session_factory()
    try:
        agent_run = (
            db.query(AgentRunModel)
            .filter(AgentRunModel.project_id == uuid.UUID(project["id"]))
            .filter(AgentRunModel.agent_type == "risk_analysis")
            .one()
        )
        assert agent_run.status == "succeeded"
    finally:
        db.close()


def test_a_second_tick_on_unchanged_signals_reuses_the_cache(client):
    owner = register(client, "risk-owner2@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    _create_breached_project(client, headers)

    orchestrator = CannedRiskOrchestrator()
    run_monitoring_tick(client.session_factory, orchestrator)
    run_monitoring_tick(client.session_factory, orchestrator)

    # The Decision Engine's signals didn't change between ticks - the
    # content-hash cache in risk_cache.py must skip the second call entirely.
    assert orchestrator.call_count == 1


def test_healthy_project_never_triggers_an_orchestrator_call(client):
    owner = register(client, "risk-owner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    client.post(
        "/api/v1/projects",
        json={"name": "Healthy Project", "description": "desc"},
        headers=headers,
    )

    orchestrator = CannedRiskOrchestrator()
    run_monitoring_tick(client.session_factory, orchestrator)
    assert orchestrator.call_count == 0


def test_an_archived_project_is_never_monitored_even_if_it_would_breach(client):
    owner = register(client, "risk-owner3b@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_breached_project(client, headers)

    archive_resp = client.patch(
        f"/api/v1/projects/{project['id']}", json={"status": "archived"}, headers=headers
    )
    assert archive_resp.status_code == 200
    assert archive_resp.json()["status"] == "archived"

    orchestrator = CannedRiskOrchestrator()
    run_monitoring_tick(client.session_factory, orchestrator)
    assert orchestrator.call_count == 0


def test_only_the_owner_can_approve_or_reject_a_recommendation(client):
    owner = register(client, "risk-owner4@example.com", role="project_owner")
    collaborator = register(client, "risk-collab4@example.com", role="collaborator")
    headers = auth_headers(owner["access_token"])
    collab_headers = auth_headers(collaborator["access_token"])
    project = _create_breached_project(client, headers)

    run_monitoring_tick(client.session_factory, CannedRiskOrchestrator())
    recommendation = client.get(
        f"/api/v1/projects/{project['id']}/recommendations", headers=headers
    ).json()[0]

    approve_resp = client.post(
        f"/api/v1/recommendations/{recommendation['id']}/approve", headers=collab_headers
    )
    assert approve_resp.status_code == 403

    reject_resp = client.post(
        f"/api/v1/recommendations/{recommendation['id']}/reject", headers=collab_headers
    )
    assert reject_resp.status_code == 403


def test_approving_a_recommendation_makes_it_approved(client):
    owner = register(client, "risk-owner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_breached_project(client, headers)

    run_monitoring_tick(client.session_factory, CannedRiskOrchestrator())
    recommendation = client.get(
        f"/api/v1/projects/{project['id']}/recommendations", headers=headers
    ).json()[0]

    approve_resp = client.post(
        f"/api/v1/recommendations/{recommendation['id']}/approve", headers=headers
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "approved"

    # Approving twice is rejected - only a pending recommendation can be decided on.
    second_approve = client.post(
        f"/api/v1/recommendations/{recommendation['id']}/approve", headers=headers
    )
    assert second_approve.status_code == 400


def test_get_risk_orchestrator_falls_back_to_fake_when_no_key(monkeypatch):
    """Mirrors the Planner's equivalent real-fallback test - exercised
    directly rather than through an HTTP round trip, since asserting on
    *which* orchestrator class main.py's lifespan or a background trigger
    picked isn't observable from outside."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    assert isinstance(get_risk_orchestrator(), FakeRiskOrchestrator)


def test_updating_a_task_immediately_checks_the_project_for_risk(client):
    """No manual "analyze now" endpoint exists (automatic-only, per design) -
    this proves the *immediate* path instead: a PATCH to an already-breaching
    project's task must surface a risk without ever calling
    run_monitoring_tick, i.e. without waiting for the next scheduler tick."""
    owner = register(client, "risk-owner6@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    project = _create_breached_project(client, headers)

    no_risks_yet = client.get(f"/api/v1/projects/{project['id']}/risks", headers=headers)
    assert no_risks_yet.json() == []

    milestones = client.get(f"/api/v1/projects/{project['id']}/milestones", headers=headers).json()
    tasks = client.get(f"/api/v1/milestones/{milestones[0]['id']}/tasks", headers=headers).json()

    patch_resp = client.patch(
        f"/api/v1/tasks/{tasks[0]['id']}", json={"status": "in_progress"}, headers=headers
    )
    assert patch_resp.status_code == 200

    risks = client.get(f"/api/v1/projects/{project['id']}/risks", headers=headers).json()
    assert len(risks) == 1
    assert risks[0]["category"] == "Schedule"  # FakeRiskOrchestrator's fixed output


class _CountingRiskOrchestrator:
    """Fails loudly if ever called - proves a zero-task project's immediate
    check is a genuine no-op (compute_signals never breaches with zero
    tasks), not just "happens not to find anything"."""

    def __init__(self):
        self.call_count = 0

    def analyze(self, *args, **kwargs):
        self.call_count += 1
        raise AssertionError("should never be called for a fresh, zero-task project")


def test_creating_a_project_never_calls_the_orchestrator(client):
    counting = _CountingRiskOrchestrator()
    app.dependency_overrides[get_risk_orchestrator] = lambda: counting

    owner = register(client, "risk-owner7@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])
    resp = client.post(
        "/api/v1/projects",
        json={"name": "Fresh Project", "description": "desc"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert counting.call_count == 0

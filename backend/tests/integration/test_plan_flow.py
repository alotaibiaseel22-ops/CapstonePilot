import pytest

from app.api.v1.deps import get_planning_orchestrator, get_session_factory
from app.application.ports.planning_orchestrator import MilestonePlan, PlannerOutput, TaskPlan
from app.core.config import settings
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


class CannedOrchestrator:
    """Deterministic stand-in for the real CrewAI orchestrator - proves the
    persistence/status-transition plumbing works without any network/LLM call."""

    def generate_plan(self, project_name, project_description, proposal_text):
        assert proposal_text  # the extracted proposal text really was passed through
        return PlannerOutput(
            summary="Test-generated plan rationale.",
            milestones=[
                MilestonePlan(
                    title="Milestone One",
                    days_from_start=7,
                    tasks=[
                        TaskPlan(
                            title="Task A", description="do a", priority="high", days_from_start=3
                        ),
                        TaskPlan(title="Task B", days_from_start=6),
                    ],
                ),
                MilestonePlan(
                    title="Milestone Two",
                    days_from_start=14,
                    tasks=[TaskPlan(title="Task C", days_from_start=10)],
                ),
            ],
            dependencies=["Milestone Two depends on Milestone One"],
            estimated_timeline="2 weeks.",
        )


@pytest.fixture()
def fake_client(client):
    app.dependency_overrides[get_session_factory] = lambda: client.session_factory
    app.dependency_overrides[get_planning_orchestrator] = lambda: CannedOrchestrator()
    yield client


def wait_for_job(client, headers, job_id, expected_status="succeeded"):
    for _ in range(20):
        response = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert response.status_code == 200, response.text
        body = response.json()
        if body["status"] in ("succeeded", "failed"):
            assert body["status"] == expected_status, body
            return body
    raise AssertionError(f"Job {job_id} never reached a terminal status")


def _create_project_and_generate(client, headers):
    project = client.post(
        "/api/v1/projects",
        json={"name": "Plan Flow Project", "description": "desc"},
        headers=headers,
    ).json()
    generate_resp = client.post(
        f"/api/v1/projects/{project['id']}/plan/generate",
        files={"file": ("proposal.txt", b"Build a thing that does stuff.", "text/plain")},
        headers=headers,
    )
    assert generate_resp.status_code == 202, generate_resp.text
    job_id = generate_resp.json()["job_id"]
    return project, job_id


def test_plan_generation_creates_a_proposed_plan_with_milestones_and_tasks(fake_client):
    owner = register(fake_client, "plan-owner1@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project, job_id = _create_project_and_generate(fake_client, headers)
    job = wait_for_job(fake_client, headers, job_id)
    assert job["output_ref"]["milestone_count"] == 2

    plan_resp = fake_client.get(f"/api/v1/projects/{project['id']}/plan", headers=headers)
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    assert plan["status"] == "proposed"
    assert plan["rationale"]["summary"] == "Test-generated plan rationale."
    assert plan["rationale"]["dependencies"] == ["Milestone Two depends on Milestone One"]
    assert plan["rationale"]["estimated_timeline"] == "2 weeks."

    milestones_resp = fake_client.get(
        f"/api/v1/projects/{project['id']}/milestones", headers=headers
    )
    milestones = milestones_resp.json()
    assert len(milestones) == 2
    assert {m["title"] for m in milestones} == {"Milestone One", "Milestone Two"}

    first_milestone = next(m for m in milestones if m["title"] == "Milestone One")
    tasks_resp = fake_client.get(
        f"/api/v1/milestones/{first_milestone['id']}/tasks", headers=headers
    )
    tasks = tasks_resp.json()
    assert len(tasks) == 2
    assert {t["title"] for t in tasks} == {"Task A", "Task B"}


def test_only_the_owner_can_approve_or_reject_the_plan(fake_client):
    owner = register(fake_client, "plan-owner2@example.com", role="project_owner")
    collaborator = register(fake_client, "plan-collab2@example.com", role="collaborator")
    headers = auth_headers(owner["access_token"])
    collab_headers = auth_headers(collaborator["access_token"])

    project, job_id = _create_project_and_generate(fake_client, headers)
    wait_for_job(fake_client, headers, job_id)

    approve_resp = fake_client.post(
        f"/api/v1/projects/{project['id']}/plan/approve", headers=collab_headers
    )
    assert approve_resp.status_code == 403

    reject_resp = fake_client.post(
        f"/api/v1/projects/{project['id']}/plan/reject", headers=collab_headers
    )
    assert reject_resp.status_code == 403


def test_approving_the_plan_makes_it_approved(fake_client):
    owner = register(fake_client, "plan-owner3@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project, job_id = _create_project_and_generate(fake_client, headers)
    wait_for_job(fake_client, headers, job_id)

    approve_resp = fake_client.post(
        f"/api/v1/projects/{project['id']}/plan/approve", headers=headers
    )
    assert approve_resp.status_code == 200, approve_resp.text
    assert approve_resp.json()["status"] == "approved"

    # Approving twice is rejected - only a proposed plan can be approved.
    second_approve = fake_client.post(
        f"/api/v1/projects/{project['id']}/plan/approve", headers=headers
    )
    assert second_approve.status_code == 400


def test_rejecting_the_plan_deletes_generated_milestones_and_resets_to_draft(fake_client):
    owner = register(fake_client, "plan-owner4@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project, job_id = _create_project_and_generate(fake_client, headers)
    wait_for_job(fake_client, headers, job_id)

    reject_resp = fake_client.post(
        f"/api/v1/projects/{project['id']}/plan/reject", headers=headers
    )
    assert reject_resp.status_code == 200, reject_resp.text
    assert reject_resp.json()["status"] == "draft"
    assert reject_resp.json()["rationale"] == {}

    milestones_resp = fake_client.get(
        f"/api/v1/projects/{project['id']}/milestones", headers=headers
    )
    assert milestones_resp.json() == []


def test_plan_generate_still_works_end_to_end_against_the_real_fallback_orchestrator(
    client, monkeypatch
):
    """The orchestrator itself is NOT overridden here - exercises the actual
    get_planning_orchestrator wiring, which falls back to
    FakePlanningOrchestrator whenever GEMINI_API_KEY is unset. Confirms
    the fallback itself (not just a test-only double) produces a real,
    reviewable plan. GEMINI_API_KEY is explicitly forced empty for this
    test via monkeypatch - this must stay deterministic regardless of whether
    whoever runs the suite happens to have a real key in their own backend/.env
    (a real key there is expected, e.g. for manual smoke-testing, but must
    never make this specific test start making real, paid API calls).
    session_factory still needs overriding so the background job writes to
    the test DB rather than the real one."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    # conftest defaults every test to a fake orchestrator via this same
    # dependency key - remove that override here so the real selection
    # function (checking settings.GEMINI_API_KEY) actually runs.
    del app.dependency_overrides[get_planning_orchestrator]
    app.dependency_overrides[get_session_factory] = lambda: client.session_factory

    owner = register(client, "plan-owner5@example.com", role="project_owner")
    headers = auth_headers(owner["access_token"])

    project, job_id = _create_project_and_generate(client, headers)
    job = wait_for_job(client, headers, job_id)
    assert job["output_ref"]["milestone_count"] == 3

    plan = client.get(f"/api/v1/projects/{project['id']}/plan", headers=headers).json()
    assert plan["status"] == "proposed"
    assert "Placeholder plan" in plan["rationale"]["summary"]

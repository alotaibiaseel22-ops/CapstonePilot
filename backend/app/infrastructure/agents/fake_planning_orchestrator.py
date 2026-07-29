from app.application.ports.planning_orchestrator import (
    MilestonePlan,
    PlannerOutput,
    PlanningOrchestratorPort,
    TaskPlan,
)

PLACEHOLDER_PREFIX = "[Placeholder plan — no GEMINI_API_KEY configured]"


class FakePlanningOrchestrator(PlanningOrchestratorPort):
    """Deterministic, no-network fallback used whenever GEMINI_API_KEY isn't
    set - mirrors ConsoleEmailService's fallback for SMTP_HOST unset. Keeps the
    feature usable end-to-end (and this iteration's tests fast/free) without a
    real LLM key; the summary is unmistakably labeled so it's never confused
    with a real AI-generated plan."""

    def generate_plan(
        self, project_name: str, project_description: str, proposal_text: str
    ) -> PlannerOutput:
        return PlannerOutput(
            summary=(
                f"{PLACEHOLDER_PREFIX} A generic starter plan for '{project_name}'. "
                "Add a real Gemini API key to backend/.env to generate an "
                "actual plan from the uploaded proposal."
            ),
            milestones=[
                MilestonePlan(
                    title="Requirements & Setup",
                    days_from_start=7,
                    tasks=[
                        TaskPlan(title="Confirm project scope", days_from_start=2),
                        TaskPlan(title="Set up project repository and tooling", days_from_start=5),
                    ],
                ),
                MilestonePlan(
                    title="Core Implementation",
                    days_from_start=30,
                    tasks=[
                        TaskPlan(title="Build core functionality", days_from_start=20),
                        TaskPlan(title="Write tests for core functionality", days_from_start=28),
                    ],
                ),
                MilestonePlan(
                    title="Review & Delivery",
                    days_from_start=45,
                    tasks=[
                        TaskPlan(title="Internal review and polish", days_from_start=40),
                        TaskPlan(title="Final delivery and documentation", days_from_start=45),
                    ],
                ),
            ],
            dependencies=["Core Implementation depends on Requirements & Setup"],
            estimated_timeline="Approximately 7 weeks from project start to delivery.",
        )

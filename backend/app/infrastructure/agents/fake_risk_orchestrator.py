from app.application.decision_engine.rules import ProjectSignals
from app.application.ports.risk_orchestrator import (
    RecommendationItem,
    RiskAnalysisOrchestratorPort,
    RiskAnalysisOutput,
    RiskItem,
)

PLACEHOLDER_PREFIX = "[Placeholder analysis — no GEMINI_API_KEY configured]"


class FakeRiskOrchestrator(RiskAnalysisOrchestratorPort):
    """Deterministic, no-network fallback used whenever GEMINI_API_KEY isn't
    set - mirrors FakePlanningOrchestrator. Keeps the monitoring feature
    usable end-to-end (and this iteration's tests fast/free) without a real
    LLM key; the output is unmistakably labeled so it's never confused with a
    real AI-generated analysis."""

    def analyze(
        self,
        project_name: str,
        project_description: str,
        signals: ProjectSignals,
        task_summary: str,
        dependencies_text: str,
        activity_text: str,
    ) -> RiskAnalysisOutput:
        risk = RiskItem(
            title=f"{PLACEHOLDER_PREFIX} Project behind schedule",
            category="Schedule",
            severity="medium",
            description=(
                f"{signals.overdue_tasks}/{signals.total_tasks} tasks overdue. Add a real "
                "Gemini API key to backend/.env to generate a real analysis."
            ),
        )
        recommendation = RecommendationItem(
            title="Review overdue tasks with the team",
            category="Process",
            severity="medium",
            effort="low",
            impact="medium",
            description="Schedule a sync to redistribute or reprioritize overdue work.",
            rationale="",
            risk_index=0,
        )
        return RiskAnalysisOutput(risks=[risk], recommendations=[recommendation])

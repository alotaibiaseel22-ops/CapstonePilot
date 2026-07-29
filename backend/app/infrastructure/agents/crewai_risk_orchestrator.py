from app.application.decision_engine.rules import ProjectSignals
from app.application.ports.risk_orchestrator import (
    RecommendationItem,
    RiskAnalysisOrchestratorPort,
    RiskAnalysisOutput,
    RiskItem,
)


class CrewAIRiskOrchestrator(RiskAnalysisOrchestratorPort):
    """Real implementation, backed by the CrewAI Flow. Converts the
    crewai/pydantic-shaped result into the plain dataclasses application/
    code depends on, so nothing outside infrastructure/agents/ ever imports
    crewai or pydantic for this.

    Deliberately does NOT check risk_cache itself - scheduler.py is this
    port's only caller, and it consults the cache *before* deciding whether
    to invoke analyze() at all, so a cache hit skips both the Gemini call
    and re-persisting duplicate RiskReport/Recommendation rows for a breach
    that hasn't actually changed. Caching is a scheduling/persistence
    decision here, not an orchestrator-implementation detail."""

    def analyze(
        self,
        project_name: str,
        project_description: str,
        signals: ProjectSignals,
        task_summary: str,
        dependencies_text: str,
        activity_text: str,
    ) -> RiskAnalysisOutput:
        # Deferred import, not just for a key-less boot (get_risk_orchestrator
        # already handles that) - this class is now constructed as a plain
        # FastAPI dependency on every project/task/milestone-affecting
        # request, including ones with nothing to do with AI. Importing
        # crewai's module tree at class-construction time would pay that
        # (real, multi-second on first import) cost synchronously inside an
        # unrelated HTTP request the first time it happens in a process.
        # Deferred to here, it only ever happens inside a BackgroundTask -
        # analyze() has no other caller (see docstring above).
        from app.infrastructure.agents.flows.risk_flow import RiskFlow, RiskFlowState

        days_remaining_text = (
            f"{signals.days_remaining}" if signals.days_remaining is not None else "not set"
        )
        signals_text = (
            f"days_remaining={days_remaining_text}, "
            f"progress_percent={signals.progress_percent:.0f}%, "
            f"schedule_variance={signals.schedule_variance:.2f}, "
            f"overdue_ratio={signals.overdue_ratio:.2f} "
            f"({signals.overdue_tasks}/{signals.total_tasks} tasks), "
            f"tasks: {signals.completed_tasks} completed / {signals.pending_tasks} pending, "
            f"milestones: {signals.completed_milestones} completed / "
            f"{signals.pending_milestones} pending / {signals.overdue_milestones} overdue, "
            f"workload_imbalance={signals.workload_imbalance:.2f}. "
            f"Breach reasons: {'; '.join(signals.breach_reasons) or 'none'}."
        )

        flow = RiskFlow()
        schema = flow.kickoff(
            inputs=RiskFlowState(
                project_name=project_name,
                project_description=project_description,
                signals_text=signals_text,
                task_summary=task_summary,
                dependencies_text=dependencies_text,
                activity_text=activity_text,
            ).model_dump()
        )

        output = RiskAnalysisOutput(
            risks=[
                RiskItem(
                    title=r.title,
                    category=r.category,
                    severity=r.severity,
                    description=r.description,
                )
                for r in schema.risks
            ],
            recommendations=[
                RecommendationItem(
                    title=r.title,
                    category=r.category,
                    severity=r.severity,
                    effort=r.effort,
                    impact=r.impact,
                    description=r.description,
                    rationale="",
                    risk_index=r.risk_index,
                )
                for r in schema.recommendations
            ],
        )
        return output

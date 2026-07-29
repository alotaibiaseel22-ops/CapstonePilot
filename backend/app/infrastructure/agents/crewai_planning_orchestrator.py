from app.application.ports.planning_orchestrator import (
    MilestonePlan,
    PlannerOutput,
    PlanningOrchestratorPort,
    TaskPlan,
)
from app.infrastructure.agents.plan_cache import get_cached_plan, set_cached_plan


class CrewAIPlanningOrchestrator(PlanningOrchestratorPort):
    """Real implementation, backed by the CrewAI Flow. Converts the
    crewai/pydantic-shaped result into the plain dataclasses application/
    code depends on, so nothing outside infrastructure/agents/ ever imports
    crewai or pydantic for this."""

    def generate_plan(
        self, project_name: str, project_description: str, proposal_text: str
    ) -> PlannerOutput:
        cached = get_cached_plan(project_name, project_description, proposal_text)
        if cached is not None:
            return cached

        # Deferred import - this class is constructed as a synchronous
        # FastAPI dependency on generate_plan's request itself (before the
        # 202 response is sent), so importing crewai's module tree here
        # rather than at class-construction time keeps that request fast;
        # the real cost only lands inside run_planning_job's background task.
        from app.infrastructure.agents.flows.planning_flow import PlanningFlow, PlanningFlowState

        flow = PlanningFlow()
        schema = flow.kickoff(
            inputs=PlanningFlowState(
                project_name=project_name,
                project_description=project_description,
                proposal_text=proposal_text,
            ).model_dump()
        )

        output = PlannerOutput(
            summary=schema.summary,
            milestones=[
                MilestonePlan(
                    title=m.title,
                    days_from_start=m.days_from_start,
                    estimated_duration_days=m.estimated_duration_days,
                    tasks=[
                        TaskPlan(
                            title=t.title,
                            description=t.description,
                            priority=t.priority,
                            days_from_start=t.days_from_start,
                        )
                        for t in m.tasks
                    ],
                )
                for m in schema.milestones
            ],
            dependencies=schema.dependencies,
            estimated_timeline=schema.estimated_timeline,
        )
        set_cached_plan(project_name, project_description, proposal_text, output)
        return output

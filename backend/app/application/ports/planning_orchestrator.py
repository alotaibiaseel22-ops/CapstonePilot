from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TaskPlan:
    title: str
    description: str = ""
    priority: str = "medium"
    days_from_start: int = 0


@dataclass
class MilestonePlan:
    title: str
    days_from_start: int
    tasks: list[TaskPlan] = field(default_factory=list)
    # The Planner's own estimate of how long this milestone takes, when it
    # can reasonably tell - never a calendar date, and never invented when
    # it can't. None (not a guessed number) when omitted.
    estimated_duration_days: int | None = None


@dataclass
class PlannerOutput:
    summary: str
    milestones: list[MilestonePlan] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    estimated_timeline: str = ""


class PlanningOrchestratorPort(ABC):
    """The seam between application/ and the CrewAI-specific implementation in
    infrastructure/agents/ - application code never imports crewai directly."""

    @abstractmethod
    def generate_plan(
        self, project_name: str, project_description: str, proposal_text: str
    ) -> PlannerOutput: ...

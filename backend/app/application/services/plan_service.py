import uuid
from typing import Any

from app.application.ports.milestone_repository import MilestoneRepository
from app.application.ports.plan_repository import PlanRepository
from app.application.ports.project_repository import ProjectRepository
from app.application.ports.task_repository import TaskRepository
from app.domain.entities import Plan
from app.domain.enums import PlanStatus


class ProjectNotFoundError(Exception):
    pass


class PlanNotFoundError(Exception):
    pass


class NotProjectOwnerError(Exception):
    pass


class InvalidPlanStatusError(Exception):
    pass


class PlanService:
    def __init__(
        self,
        plan_repository: PlanRepository,
        project_repository: ProjectRepository,
        milestone_repository: MilestoneRepository,
        task_repository: TaskRepository,
    ):
        self._plans = plan_repository
        self._projects = project_repository
        self._milestones = milestone_repository
        self._tasks = task_repository

    def get_current_plan(self, project_id: uuid.UUID) -> Plan:
        plan = self._plans.get_current_for_project(project_id)
        if plan is None:
            raise PlanNotFoundError(f"No plan found for project {project_id}")
        return plan

    def _assert_owner(self, project_id: uuid.UUID, requesting_user_id: uuid.UUID) -> None:
        project = self._projects.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found")
        if project.owner_id != requesting_user_id:
            raise NotProjectOwnerError("Only this project's owner can do that")

    def mark_proposed(self, plan_id: uuid.UUID, rationale: dict[str, Any]) -> Plan:
        """Called by the Planner orchestrator once it has generated milestones/tasks
        for this plan - moves it from the empty draft created at project-creation
        time into "awaiting owner review", per the architecture's human-in-the-loop
        approval gate. Never called directly from an HTTP route."""
        plan = self._plans.get_by_id(plan_id)
        if plan is None:
            raise PlanNotFoundError(f"Plan {plan_id} not found")
        plan.status = PlanStatus.PROPOSED
        plan.rationale = rationale
        return self._plans.update(plan)

    def approve_plan(self, project_id: uuid.UUID, requesting_user_id: uuid.UUID) -> Plan:
        self._assert_owner(project_id, requesting_user_id)
        plan = self.get_current_plan(project_id)
        if plan.status != PlanStatus.PROPOSED:
            raise InvalidPlanStatusError("Only a proposed plan can be approved")
        plan.status = PlanStatus.APPROVED
        return self._plans.update(plan)

    def reject_plan(self, project_id: uuid.UUID, requesting_user_id: uuid.UUID) -> Plan:
        """Rejecting discards what the Planner generated rather than leaving a
        half-approved plan around - it resets the plan to the same empty draft
        state project-creation started with, so a fresh proposal can replace it."""
        self._assert_owner(project_id, requesting_user_id)
        plan = self.get_current_plan(project_id)
        if plan.status != PlanStatus.PROPOSED:
            raise InvalidPlanStatusError("Only a proposed plan can be rejected")

        for milestone in self._milestones.list_by_plan(plan.id):
            for task in self._tasks.list_by_milestone(milestone.id):
                self._tasks.delete(task.id)
            self._milestones.delete(milestone.id)

        plan.status = PlanStatus.DRAFT
        plan.rationale = {}
        return self._plans.update(plan)

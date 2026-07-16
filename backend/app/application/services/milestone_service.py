import uuid
from datetime import UTC, date, datetime

from app.application.ports.milestone_repository import MilestoneRepository
from app.application.ports.plan_repository import PlanRepository
from app.domain.entities import Milestone


class MilestoneNotFoundError(Exception):
    pass


class MilestoneService:
    def __init__(self, milestone_repository: MilestoneRepository, plan_repository: PlanRepository):
        self._milestones = milestone_repository
        self._plans = plan_repository

    def create_milestone(
        self,
        project_id: uuid.UUID,
        title: str,
        due_date: date | None,
        order: int = 0,
    ) -> Milestone:
        plan = self._plans.get_current_for_project(project_id)
        if plan is None:
            raise ValueError(f"No plan found for project {project_id}")

        milestone = Milestone(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title=title,
            due_date=due_date,
            order=order,
            created_at=datetime.now(UTC),
        )
        return self._milestones.create(milestone)

    def list_milestones(self, project_id: uuid.UUID) -> list[Milestone]:
        plan = self._plans.get_current_for_project(project_id)
        if plan is None:
            return []
        return self._milestones.list_by_plan(plan.id)

    def get_milestone(self, milestone_id: uuid.UUID) -> Milestone:
        milestone = self._milestones.get_by_id(milestone_id)
        if milestone is None:
            raise MilestoneNotFoundError(f"Milestone {milestone_id} not found")
        return milestone

    def update_milestone(
        self,
        milestone_id: uuid.UUID,
        title: str | None = None,
        due_date: date | None = None,
        order: int | None = None,
    ) -> Milestone:
        milestone = self.get_milestone(milestone_id)
        if title is not None:
            milestone.title = title
        if due_date is not None:
            milestone.due_date = due_date
        if order is not None:
            milestone.order = order
        return self._milestones.update(milestone)

    def delete_milestone(self, milestone_id: uuid.UUID) -> None:
        self._milestones.delete(milestone_id)

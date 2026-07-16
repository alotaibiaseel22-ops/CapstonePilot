"""Seed the local dev database with demo data matching the frontend's mock UI.

Run with: python scripts/seed.py (from backend/, with the venv activated).
Safe to re-run: exits early if the demo owner account already exists.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.services.auth_service import AuthService  # noqa: E402
from app.application.services.invitation_service import InvitationService  # noqa: E402
from app.application.services.milestone_service import MilestoneService  # noqa: E402
from app.application.services.project_service import ProjectService  # noqa: E402
from app.application.services.task_service import TaskService  # noqa: E402
from app.domain.enums import TaskPriority, UserRole  # noqa: E402
from app.infrastructure.db.repositories.invitation_repository import (  # noqa: E402
    SqlAlchemyInvitationRepository,
)
from app.infrastructure.db.repositories.milestone_repository import (  # noqa: E402
    SqlAlchemyMilestoneRepository,
)
from app.infrastructure.db.repositories.plan_repository import (
    SqlAlchemyPlanRepository,  # noqa: E402
)
from app.infrastructure.db.repositories.project_member_repository import (  # noqa: E402
    SqlAlchemyProjectMemberRepository,
)
from app.infrastructure.db.repositories.project_repository import (  # noqa: E402
    SqlAlchemyProjectRepository,
)
from app.infrastructure.db.repositories.task_repository import (
    SqlAlchemyTaskRepository,  # noqa: E402
)
from app.infrastructure.db.repositories.user_repository import (
    SqlAlchemyUserRepository,  # noqa: E402
)
from app.infrastructure.db.session import SessionLocal  # noqa: E402
from app.infrastructure.email.email_service import build_email_service  # noqa: E402

MILESTONES = [
    {
        "title": "Requirements & Research",
        "due_date": "2026-07-19",
        "tasks": [
            ("Gather stakeholder requirements", TaskPriority.HIGH),
            ("Literature review on traffic prediction models", TaskPriority.MEDIUM),
            ("Define success metrics", TaskPriority.MEDIUM),
            ("Finalize project scope document", TaskPriority.HIGH),
        ],
    },
    {
        "title": "Data Pipeline & Preprocessing",
        "due_date": "2026-08-02",
        "tasks": [
            ("Collect traffic sensor data", TaskPriority.HIGH),
            ("Clean and normalize dataset", TaskPriority.HIGH),
            ("Feature engineering", TaskPriority.MEDIUM),
            ("Train/test split and validation strategy", TaskPriority.MEDIUM),
        ],
    },
    {
        "title": "Model Development",
        "due_date": "2026-08-23",
        "tasks": [
            ("Implement LSTM baseline model", TaskPriority.HIGH),
            ("Hyperparameter tuning", TaskPriority.MEDIUM),
            ("Model evaluation and benchmarking", TaskPriority.HIGH),
            ("Integrate real-time prediction API", TaskPriority.HIGH),
        ],
    },
    {
        "title": "Dashboard & Frontend",
        "due_date": "2026-09-13",
        "tasks": [
            ("Design UI wireframes", TaskPriority.MEDIUM),
            ("Build React dashboard components", TaskPriority.HIGH),
            ("Integrate map visualization", TaskPriority.MEDIUM),
            ("Connect to backend API", TaskPriority.HIGH),
        ],
    },
    {
        "title": "Testing & Deployment",
        "due_date": "2026-10-01",
        "tasks": [
            ("Write unit and integration test plan", TaskPriority.HIGH),
            ("Set up CI pipeline", TaskPriority.MEDIUM),
            ("User acceptance testing", TaskPriority.MEDIUM),
            ("Deploy to production", TaskPriority.HIGH),
        ],
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        auth_service = AuthService(SqlAlchemyUserRepository(db))
        project_service = ProjectService(
            SqlAlchemyProjectRepository(db),
            SqlAlchemyPlanRepository(db),
            SqlAlchemyProjectMemberRepository(db),
            SqlAlchemyInvitationRepository(db),
            SqlAlchemyMilestoneRepository(db),
            SqlAlchemyTaskRepository(db),
        )
        invitation_service = InvitationService(
            SqlAlchemyInvitationRepository(db),
            SqlAlchemyProjectMemberRepository(db),
            SqlAlchemyUserRepository(db),
            SqlAlchemyProjectRepository(db),
            build_email_service(),
        )
        milestone_service = MilestoneService(
            SqlAlchemyMilestoneRepository(db), SqlAlchemyPlanRepository(db)
        )
        task_service = TaskService(SqlAlchemyTaskRepository(db))

        existing = SqlAlchemyUserRepository(db).get_by_email("sarah@capstonepilot.dev")
        if existing is not None:
            print("Seed data already present (sarah@capstonepilot.dev exists) - skipping.")
            return

        owner = auth_service.register(
            name="Sarah Ahmed",
            email="sarah@capstonepilot.dev",
            password="capstone123",
            role=UserRole.PROJECT_OWNER,
        )
        collaborators = []
        for name, email in [
            ("Omar Al-Rashidi", "omar@capstonepilot.dev"),
            ("Priya Nair", "priya@capstonepilot.dev"),
            ("Lena Fischer", "lena@capstonepilot.dev"),
        ]:
            user = auth_service.register(
                name=name, email=email, password="capstone123", role=UserRole.COLLABORATOR
            )
            collaborators.append(user)
        print(f"Created 4 users (project owner: {owner.email})")

        project = project_service.create_project(
            name="ML-Based Traffic Optimization",
            description=(
                "A machine learning system that analyzes real-time traffic data to optimize "
                "signal timing and reduce congestion in urban intersections. The system will "
                "use LSTM neural networks for prediction and a React-based dashboard for "
                "monitoring."
            ),
            owner_id=owner.id,
            start_date=date.fromisoformat("2026-07-15"),
            due_date=date.fromisoformat("2026-12-01"),
        )
        print(f"Created project: {project.name} ({project.id})")

        # Demonstrates the real invite -> accept flow rather than bypassing it:
        # each collaborator is invited by email, then accepts, same as a real user would.
        for user in collaborators:
            invitation = invitation_service.invite_by_email(project.id, user.email, owner.id)
            invitation_service.accept_invitation(invitation.token, user)
        print(f"Invited and joined {len(collaborators)} collaborators to the project")

        for order, milestone_data in enumerate(MILESTONES):
            milestone = milestone_service.create_milestone(
                project_id=project.id,
                title=milestone_data["title"],
                due_date=date.fromisoformat(milestone_data["due_date"]),
                order=order,
            )
            for title, priority in milestone_data["tasks"]:
                task_service.create_task(milestone_id=milestone.id, title=title, priority=priority)
        print(f"Created {len(MILESTONES)} milestones with tasks")

        print("\nSeed complete. Log in with sarah@capstonepilot.dev / capstone123")
    finally:
        db.close()


if __name__ == "__main__":
    main()

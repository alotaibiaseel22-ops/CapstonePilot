"""add cascade delete to project child foreign keys

Revision ID: abadb1551d72
Revises: 4c7f9a2e6b1d
Create Date: 2026-08-05 10:52:41.771460

Fixes a real production bug: deleting a project returned 500 with a foreign
key IntegrityError, because `agent_runs.project_id` had no ON DELETE
behavior at the database level and application code (ProjectService.
delete_project) never deleted agent_runs rows before deleting the project -
Postgres always enforces FKs, so an orphaned agent_runs row blocked the
DELETE. As a defense-in-depth fix (not just patching that one table), this
adds ondelete="CASCADE" to every FK in the project -> plan -> milestone ->
task chain, so the database itself now guarantees cleanup regardless of
whether application code remembers to delete a given child table. FKs to
users.id (owner_id, invited_by, assignee_id, etc.) are deliberately left
untouched - deleting a user must never cascade-delete projects or unrelated
records.

The original FKs were all created unnamed (no explicit name= on
ForeignKey(...)), so SQLite reflects them with name=None and Postgres
assigns its own default name - neither can be targeted by a hardcoded DROP
CONSTRAINT. A naming_convention is supplied to batch_alter_table so the
anonymous constraint gets a deterministic, targetable name at migration-run
time on whichever backend is actually running; each is then dropped and
recreated with an explicit name plus ondelete="CASCADE" in the same batch.
Confirmed working end-to-end against a real copy of this project's SQLite
dev database (including that deleting a project with an agent_runs row no
longer raises) before being committed here.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "abadb1551d72"
down_revision: Union[str, Sequence[str], None] = "4c7f9a2e6b1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NAMING_CONVENTION = {"fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"}

# (table, column, referred_table) for every FK that should now cascade -
# every table that references projects.id directly, plus the two
# transitive links (milestones -> plans, tasks -> milestones) so the
# cascade chain is unbroken all the way down from a project.
_CASCADE_FKS = [
    ("agent_runs", "project_id", "projects"),
    ("plans", "project_id", "projects"),
    ("risk_reports", "project_id", "projects"),
    ("recommendations", "project_id", "projects"),
    ("recommendations", "risk_report_id", "risk_reports"),
    ("project_members", "project_id", "projects"),
    ("invitations", "project_id", "projects"),
    ("activity_events", "project_id", "projects"),
    ("milestones", "plan_id", "plans"),
    ("tasks", "milestone_id", "milestones"),
]


def _fk_name(table: str, column: str, referred_table: str) -> str:
    return f"fk_{table}_{column}_{referred_table}"


def upgrade() -> None:
    """Upgrade schema."""
    for table, column, referred_table in _CASCADE_FKS:
        name = _fk_name(table, column, referred_table)
        with op.batch_alter_table(
            table, schema=None, naming_convention=_NAMING_CONVENTION
        ) as batch_op:
            batch_op.drop_constraint(name, type_="foreignkey")
            batch_op.create_foreign_key(
                name, referred_table, [column], ["id"], ondelete="CASCADE"
            )


def downgrade() -> None:
    """Downgrade schema."""
    for table, column, referred_table in reversed(_CASCADE_FKS):
        name = _fk_name(table, column, referred_table)
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_constraint(name, type_="foreignkey")
            batch_op.create_foreign_key(name, referred_table, [column], ["id"])

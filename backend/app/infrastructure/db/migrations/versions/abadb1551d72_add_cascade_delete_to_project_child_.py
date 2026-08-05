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
ForeignKey(...)/ForeignKeyConstraint(...)). SQLite reflects an unnamed FK as
name=None (SQLite has no real constraint-name concept at all - names in DDL
are accepted but discarded), so a naming_convention passed to
batch_alter_table can synthesize a deterministic name for it there. Postgres
is different: it assigns its own real, permanent default name
(`<table>_<column>_fkey`) to an unnamed FK at CREATE TABLE time, and that
name is what actually lives in the catalog - passing naming_convention to
batch_alter_table does NOT rename an already-named constraint, it only
fills in a name for a reflected constraint that has none. An earlier version
of this migration hardcoded the `fk_...` name for the DROP on the assumption
it would match on every backend; it matched on SQLite (where the anonymous
constraint gets synthesized to exactly that name) but not on Postgres, where
the real name is `agent_runs_project_id_fkey` etc., producing
`psycopg2.errors.UndefinedObject: constraint "fk_agent_runs_project_id_projects"
does not exist` on the very first production deploy. Every one of the 10
entries below had the identical flaw, not just agent_runs - it just failed
on the first one reached.

Fixed by looking up each constraint's real, current name via
sqlalchemy.inspect() at migration-run time instead of assuming one: drop
whatever is actually there (skipping the drop entirely if nothing matches,
so this is safe to run against a database where the constraint is already
missing or already migrated), then (re)create it with the deterministic
`fk_...` name and ondelete="CASCADE". Same treatment applied to downgrade()
for symmetry/idempotency. Verified end-to-end on a real copy of this
project's SQLite dev database (upgrade, downgrade, re-upgrade, each
idempotent; deleting a project with an agent_runs row no longer raises) and
via a standalone unit test of the lookup helper against a mocked Postgres-
shaped inspector response (real name `agent_runs_project_id_fkey`, distinct
from the `fk_...` target name) to prove the Postgres branch is exercised
correctly - no live Postgres instance was available in this environment to
run the migration against directly.
"""

from typing import Sequence, Union

import sqlalchemy as sa
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


def _find_existing_fk(inspector, table: str, column: str, referred_table: str) -> tuple[bool, str | None]:
    """Looks up the FK constraint actually on (table.column -> referred_table.id)
    right now, whatever it's really named. Returns (found, name) - name is
    None on SQLite even when found (SQLite has no queryable constraint-name
    concept), which the caller treats as "let batch_alter_table's
    naming_convention supply the name for this drop" rather than "nothing to
    drop". Returns (False, None) when no matching FK exists at all, so the
    caller can safely skip the drop instead of erroring on a database where
    it's already missing."""
    for fk in inspector.get_foreign_keys(table):
        if fk.get("referred_table") == referred_table and fk.get("constrained_columns") == [
            column
        ]:
            return True, fk.get("name")
    return False, None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table, column, referred_table in _CASCADE_FKS:
        target_name = _fk_name(table, column, referred_table)
        found, existing_name = _find_existing_fk(inspector, table, column, referred_table)
        with op.batch_alter_table(
            table, schema=None, naming_convention=_NAMING_CONVENTION
        ) as batch_op:
            if found:
                # Drop whatever is really there: the DB's real name if it has
                # one (Postgres), or target_name as synthesized for the
                # anonymous constraint by naming_convention above (SQLite).
                batch_op.drop_constraint(existing_name or target_name, type_="foreignkey")
            batch_op.create_foreign_key(
                target_name, referred_table, [column], ["id"], ondelete="CASCADE"
            )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table, column, referred_table in reversed(_CASCADE_FKS):
        target_name = _fk_name(table, column, referred_table)
        found, existing_name = _find_existing_fk(inspector, table, column, referred_table)
        with op.batch_alter_table(
            table, schema=None, naming_convention=_NAMING_CONVENTION
        ) as batch_op:
            if found:
                batch_op.drop_constraint(existing_name or target_name, type_="foreignkey")
            batch_op.create_foreign_key(target_name, referred_table, [column], ["id"])

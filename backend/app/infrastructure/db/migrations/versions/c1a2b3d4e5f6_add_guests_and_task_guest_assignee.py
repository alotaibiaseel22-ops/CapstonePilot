"""add guests table and tasks.assignee_guest_id

Revision ID: c1a2b3d4e5f6
Revises: abadb1551d72
Create Date: 2026-08-05 14:00:00.000000

Adds the "guest" identity for the Figma/Canva-style shareable-link access
redesign: a guest is explicitly not a User (no email/password/login), bound
to exactly one project via the invitation it was created from. Purely
additive - a new table plus one new nullable FK column on tasks - no
backfill, no existing row touched.

Every new FK here is given an explicit name (unlike several older
migrations' bare ForeignKey(...) calls, which get silently different
default names on SQLite vs Postgres - see abadb1551d72's own postmortem
comment) so it can always be targeted directly if it ever needs to change.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2b3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'abadb1551d72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'guests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('invitation_id', sa.Uuid(), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['project_id'], ['projects.id'], name='fk_guests_project_id_projects',
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['invitation_id'], ['invitations.id'], name='fk_guests_invitation_id_invitations',
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_guests_project_id'), 'guests', ['project_id'], unique=False)
    op.create_index(op.f('ix_guests_invitation_id'), 'guests', ['invitation_id'], unique=False)

    # SQLite has no direct ALTER TABLE ADD CONSTRAINT - batch mode is
    # required (does a copy-and-move rebuild there; on Postgres/other
    # ALTER-capable backends Alembic auto-detects support and issues plain
    # ALTER statements instead, same as every other batch_alter_table use
    # in this project's migrations).
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assignee_guest_id', sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            'fk_tasks_assignee_guest_id_guests', 'guests', ['assignee_guest_id'], ['id'],
            ondelete='SET NULL',
        )
        batch_op.create_check_constraint(
            'ck_tasks_single_assignee', 'assignee_id IS NULL OR assignee_guest_id IS NULL',
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('ck_tasks_single_assignee', type_='check')
        batch_op.drop_constraint('fk_tasks_assignee_guest_id_guests', type_='foreignkey')
        batch_op.drop_column('assignee_guest_id')

    op.drop_index(op.f('ix_guests_invitation_id'), table_name='guests')
    op.drop_index(op.f('ix_guests_project_id'), table_name='guests')
    op.drop_table('guests')

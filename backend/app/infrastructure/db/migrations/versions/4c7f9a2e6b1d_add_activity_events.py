"""add activity events

Revision ID: 4c7f9a2e6b1d
Revises: 9e2a5c7f1b3d
Create Date: 2026-07-23 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c7f9a2e6b1d'
down_revision: Union[str, Sequence[str], None] = '9e2a5c7f1b3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('activity_events',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('project_id', sa.Uuid(), nullable=False),
    sa.Column('actor_id', sa.Uuid(), nullable=True),
    sa.Column('event_type', sa.String(length=32), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activity_events_project_id'), 'activity_events', ['project_id'], unique=False)
    op.create_index(op.f('ix_activity_events_created_at'), 'activity_events', ['created_at'], unique=False)

    op.add_column('users', sa.Column('notifications_last_seen_at', sa.DateTime(), nullable=True))
    # Backfill so existing users start "caught up" as of now, rather than
    # showing a flood of retroactive unread activity the moment this ships.
    op.execute('UPDATE users SET notifications_last_seen_at = created_at WHERE notifications_last_seen_at IS NULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'notifications_last_seen_at')
    op.drop_index(op.f('ix_activity_events_created_at'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_project_id'), table_name='activity_events')
    op.drop_table('activity_events')

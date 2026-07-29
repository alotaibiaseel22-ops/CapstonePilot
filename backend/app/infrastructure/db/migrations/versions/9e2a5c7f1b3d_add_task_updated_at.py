"""add task updated_at

Revision ID: 9e2a5c7f1b3d
Revises: f872711ef2af
Create Date: 2026-07-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e2a5c7f1b3d'
down_revision: Union[str, Sequence[str], None] = 'f872711ef2af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tasks', sa.Column('updated_at', sa.DateTime(), nullable=True))
    # Backfill existing rows so the Decision Engine's inactivity signal never
    # sees a null updated_at - a task that predates this column is treated as
    # last touched when it was created.
    op.execute('UPDATE tasks SET updated_at = created_at WHERE updated_at IS NULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tasks', 'updated_at')

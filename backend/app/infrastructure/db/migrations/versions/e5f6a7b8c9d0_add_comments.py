"""add comments

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-06 09:05:00.000000

Project-wide discussion comments (not per-task). Same "exactly one author,
never both, never neither" rule as attachments.uploader_id/
uploader_guest_id - see that migration's docstring for why this differs
from tasks.ck_tasks_single_assignee.

Purely additive - one new table, no existing row touched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'comments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('author_id', sa.Uuid(), nullable=True),
        sa.Column('author_guest_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['project_id'], ['projects.id'], name='fk_comments_project_id_projects',
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['author_id'], ['users.id'], name='fk_comments_author_id_users',
        ),
        sa.ForeignKeyConstraint(
            ['author_guest_id'], ['guests.id'], name='fk_comments_author_guest_id_guests',
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            '(author_id IS NOT NULL AND author_guest_id IS NULL) OR '
            '(author_id IS NULL AND author_guest_id IS NOT NULL)',
            name='ck_comments_exactly_one_author',
        ),
    )
    op.create_index(op.f('ix_comments_project_id'), 'comments', ['project_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_comments_project_id'), table_name='comments')
    op.drop_table('comments')

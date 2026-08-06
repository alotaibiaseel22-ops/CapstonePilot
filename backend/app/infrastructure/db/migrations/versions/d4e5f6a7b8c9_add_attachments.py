"""add attachments and attachment_blobs

Revision ID: d4e5f6a7b8c9
Revises: c1a2b3d4e5f6
Create Date: 2026-08-06 09:00:00.000000

Persistent project file attachments. File bytes live in a separate
attachment_blobs table (1:1 with attachments via a shared primary key) so a
plain listing query against attachments alone never pulls blob bytes across
the wire - there's no clean column-deferral idiom in this codebase's
legacy session.query() style as reliable as just not joining the blob
table at all.

An attachment always has an uploader - exactly one of uploader_id/
uploader_guest_id is set, never both, never neither (ck_attachments_
exactly_one_uploader). This is stricter than tasks.ck_tasks_single_assignee,
which allows both null (unassigned) - an attachment can't exist without
someone having uploaded it.

Purely additive - two new tables, no existing row touched.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c1a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'attachments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=255), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('uploader_id', sa.Uuid(), nullable=True),
        sa.Column('uploader_guest_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['project_id'], ['projects.id'], name='fk_attachments_project_id_projects',
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['uploader_id'], ['users.id'], name='fk_attachments_uploader_id_users',
        ),
        sa.ForeignKeyConstraint(
            ['uploader_guest_id'], ['guests.id'], name='fk_attachments_uploader_guest_id_guests',
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            '(uploader_id IS NOT NULL AND uploader_guest_id IS NULL) OR '
            '(uploader_id IS NULL AND uploader_guest_id IS NOT NULL)',
            name='ck_attachments_exactly_one_uploader',
        ),
    )
    op.create_index(op.f('ix_attachments_project_id'), 'attachments', ['project_id'], unique=False)

    op.create_table(
        'attachment_blobs',
        sa.Column('attachment_id', sa.Uuid(), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.ForeignKeyConstraint(
            ['attachment_id'], ['attachments.id'], name='fk_attachment_blobs_attachment_id_attachments',
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('attachment_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('attachment_blobs')
    op.drop_index(op.f('ix_attachments_project_id'), table_name='attachments')
    op.drop_table('attachments')

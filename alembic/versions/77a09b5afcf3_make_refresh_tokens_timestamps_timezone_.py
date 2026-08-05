"""make refresh_tokens timestamps timezone-aware

Revision ID: 77a09b5afcf3
Revises: 3bc1de7d6b21
Create Date: 2026-08-05 09:32:35.500478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '77a09b5afcf3'
down_revision: Union[str, Sequence[str], None] = '3bc1de7d6b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'refresh_tokens', 'expires_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        'refresh_tokens', 'created_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text('now()'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'refresh_tokens', 'created_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
        existing_server_default=sa.text('now()'),
    )
    op.alter_column(
        'refresh_tokens', 'expires_at',
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
    )

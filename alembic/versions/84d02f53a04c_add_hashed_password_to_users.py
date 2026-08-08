"""add hashed_password to users

Revision ID: 84d02f53a04c
Revises: 1f3c9a2b7d84
Create Date: 2026-07-20 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84d02f53a04c'
down_revision: Union[str, Sequence[str], None] = '1f3c9a2b7d84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('hashed_password', sa.String(length=255), nullable=False, server_default=''),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'hashed_password')

"""add oauth accounts table

Revision ID: 8db3d186dce9
Revises: 5da23629c0bd
Create Date: 2026-08-08 14:28:27.948396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8db3d186dce9'
down_revision: Union[str, Sequence[str], None] = '5da23629c0bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "oauth_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id"),
    )
    op.drop_constraint("users_google_id_key", "users", type_="unique")
    op.drop_column("users", "google_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))
    op.create_unique_constraint("users_google_id_key", "users", ["google_id"])
    op.drop_table("oauth_accounts")

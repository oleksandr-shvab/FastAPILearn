"""add editor role and members add permission

Revision ID: 2a20c9baf15a
Revises: 380286d3b09e
Create Date: 2026-08-10 11:49:27.444961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a20c9baf15a'
down_revision: Union[str, Sequence[str], None] = '380286d3b09e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "INSERT INTO permissions (codename, description) VALUES "
        "('project.members.add', 'Add new members to the project')"
    )
    op.execute(
        "INSERT INTO roles (name, description) VALUES "
        "('editor', 'Can add project members but cannot change or remove existing ones')"
    )
    op.execute(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id FROM roles r, permissions p "
        "WHERE r.name IN ('owner', 'editor') AND p.codename = 'project.members.add'"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM roles WHERE name = 'editor'")
    op.execute("DELETE FROM permissions WHERE codename = 'project.members.add'")

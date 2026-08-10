"""add roles and permissions

Revision ID: 380286d3b09e
Revises: 0c7e8a2d5c55
Create Date: 2026-08-10 10:21:43.582979

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '380286d3b09e'
down_revision: Union[str, Sequence[str], None] = '0c7e8a2d5c55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codename", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codename"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    op.execute(
        "INSERT INTO roles (name, description) VALUES "
        "('owner', 'Full control over the project, including managing members'), "
        "('member', 'Regular project member without management rights')"
    )
    op.execute(
        "INSERT INTO permissions (codename, description) VALUES "
        "('project.members.manage', 'Add, remove, and change the role of project members')"
    )
    op.execute(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id FROM roles r, permissions p "
        "WHERE r.name = 'owner' AND p.codename = 'project.members.manage'"
    )

    op.add_column("project_members", sa.Column("role_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("project_members_role_id_fkey"), "project_members", "roles", ["role_id"], ["id"]
    )
    op.execute(
        "UPDATE project_members SET role_id = "
        "(SELECT id FROM roles WHERE name = project_members.role::text)"
    )
    op.alter_column("project_members", "role_id", nullable=False)

    op.drop_column("project_members", "role")
    op.execute("DROP TYPE project_role")


def downgrade() -> None:
    """Downgrade schema."""
    project_role = sa.Enum("owner", "member", name="project_role")
    project_role.create(op.get_bind(), checkfirst=True)
    op.add_column("project_members", sa.Column("role", project_role, nullable=True))
    op.execute(
        "UPDATE project_members pm SET role = r.name::project_role "
        "FROM roles r WHERE r.id = pm.role_id"
    )
    op.alter_column("project_members", "role", nullable=False)

    op.drop_constraint(op.f("project_members_role_id_fkey"), "project_members", type_="foreignkey")
    op.drop_column("project_members", "role_id")

    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")

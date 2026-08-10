import strawberry
from sqlalchemy import select
from strawberry.types import Info

from app.models import Project


@strawberry.type
class RoleType:
    id: int
    name: str
    description: str | None


@strawberry.type
class UserType:
    id: int
    username: str
    email: str
    is_admin: bool


@strawberry.type
class ProjectMemberType:
    id: int
    user_id: strawberry.Private[int]
    role_id: strawberry.Private[int]

    @strawberry.field
    async def user(self, info: Info) -> UserType:
        # Naive: one SELECT per member -> N+1 across a project's member list.
        #   result = await info.context["db"].execute(
        #       select(User).where(User.id == self.user_id)
        #   )
        #   user = result.scalar_one()
        # DataLoader instead batches every `.load(user_id)` call made while
        # resolving this request into a single `WHERE id IN (...)` query.
        user = await info.context["user_loader"].load(self.user_id)
        return UserType(
            id=user.id, username=user.username, email=user.email, is_admin=user.is_admin
        )

    @strawberry.field
    async def role(self, info: Info) -> RoleType:
        # Same batching trick as `user` above, keyed by role_id instead.
        role = await info.context["role_loader"].load(self.role_id)
        return RoleType(id=role.id, name=role.name, description=role.description)


@strawberry.type
class ProjectType:
    id: int
    name: str

    @strawberry.field
    async def members(self, info: Info) -> list[ProjectMemberType]:
        # Naive: one SELECT per project -> N+1 when listing many projects.
        #   result = await info.context["db"].execute(
        #       select(ProjectMember).where(ProjectMember.project_id == self.id)
        #   )
        #   members = result.scalars().all()
        # DataLoader instead collects every `.load(project_id)` call made
        # during this request's tick and fires ONE
        # `WHERE project_id IN (...)` query for all of them at once.
        members = await info.context["member_loader"].load(self.id)
        return [
            ProjectMemberType(id=member.id, user_id=member.user_id, role_id=member.role_id)
            for member in members
        ]


@strawberry.type
class Query:
    @strawberry.field
    async def projects(self, info: Info) -> list[ProjectType]:
        result = await info.context["db"].execute(select(Project))
        return [ProjectType(id=p.id, name=p.name) for p in result.scalars().all()]

    @strawberry.field
    async def project(self, info: Info, id: int) -> ProjectType | None:
        project = await info.context["db"].get(Project, id)
        return ProjectType(id=project.id, name=project.name) if project else None

    @strawberry.field
    async def me(self, info: Info) -> UserType:
        user = info.context["current_user"]
        return UserType(
            id=user.id, username=user.username, email=user.email, is_admin=user.is_admin
        )


schema = strawberry.Schema(query=Query)

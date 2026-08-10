from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud import role as role_crud
from app.crud import user as user_crud
from app.enums import ProjectPermission
from app.exceptions import LastOwnerError, MembershipAlreadyExistsError, MembershipNotFoundError
from app.filters import ProjectFilterParams
from app.models import Project, ProjectMember, User
from app.models.role import Permission, Role, role_permissions
from app.schemas import ProjectCreate, ProjectMemberRead, ProjectRead
from app.utils import apply_filters, apply_ordering


async def create_project(session: AsyncSession, payload: ProjectCreate, owner: User) -> ProjectRead:
    owner_role = await role_crud.get_role_by_name(session, "owner")
    project = Project(name=payload.name)
    project.members.append(ProjectMember(user=owner, role=owner_role))
    session.add(project)
    await session.commit()
    return ProjectRead.model_validate(project)


async def list_projects(session: AsyncSession, filters: ProjectFilterParams) -> list[ProjectRead]:
    query = select(Project).options(selectinload(Project.members).selectinload(ProjectMember.user))
    query = apply_filters(query, Project, filters)
    query = apply_ordering(query, Project, filters.order_by)
    result = await session.execute(query)
    return [ProjectRead.model_validate(project) for project in result.scalars().all()]


async def list_projects_for_user(
    session: AsyncSession, user_id: int, filters: ProjectFilterParams
) -> list[ProjectRead]:
    query = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user_id)
        .options(selectinload(Project.members).selectinload(ProjectMember.user))
    )
    query = apply_filters(query, Project, filters)
    query = apply_ordering(query, Project, filters.order_by)
    result = await session.execute(query)
    return [ProjectRead.model_validate(project) for project in result.scalars().all()]


async def get_membership(
    session: AsyncSession, project_id: int, user_id: int
) -> ProjectMember | None:
    result = await session.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def list_members(session: AsyncSession, project_id: int) -> list[ProjectMemberRead]:
    result = await session.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .options(selectinload(ProjectMember.user))
    )
    return [ProjectMemberRead.model_validate(member) for member in result.scalars().all()]


async def add_member(
    session: AsyncSession, project_id: int, user_id: int, role_name: str
) -> ProjectMemberRead:
    user = await user_crud.get_user(session, user_id)
    role = await role_crud.get_role_by_name(session, role_name)
    member = ProjectMember(project_id=project_id, user=user, role=role)
    session.add(member)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise MembershipAlreadyExistsError(project_id, user_id)
    return ProjectMemberRead.model_validate(member)


async def update_member_role(
    session: AsyncSession, project_id: int, user_id: int, role_name: str
) -> ProjectMemberRead:
    member = await get_membership(session, project_id, user_id)
    if member is None:
        raise MembershipNotFoundError(project_id, user_id)
    new_role = await role_crud.get_role_by_name(session, role_name)
    was_manager = member.has_permission(ProjectPermission.MEMBERS_MANAGE.value)
    will_be_manager = any(
        p.codename == ProjectPermission.MEMBERS_MANAGE.value for p in new_role.permissions
    )
    if was_manager and not will_be_manager:
        await _ensure_not_last_manager(session, project_id, excluding_user_id=user_id)
    member.role = new_role
    await session.commit()
    await session.refresh(member, attribute_names=["user"])
    return ProjectMemberRead.model_validate(member)


async def remove_member(session: AsyncSession, project_id: int, user_id: int) -> None:
    member = await get_membership(session, project_id, user_id)
    if member is None:
        raise MembershipNotFoundError(project_id, user_id)
    if member.has_permission(ProjectPermission.MEMBERS_MANAGE.value):
        await _ensure_not_last_manager(session, project_id, excluding_user_id=user_id)
    await session.delete(member)
    await session.commit()


async def _ensure_not_last_manager(
    session: AsyncSession, project_id: int, excluding_user_id: int
) -> None:
    result = await session.execute(
        select(func.count(func.distinct(ProjectMember.id)))
        .select_from(ProjectMember)
        .join(Role, ProjectMember.role_id == Role.id)
        .join(role_permissions, role_permissions.c.role_id == Role.id)
        .join(Permission, Permission.id == role_permissions.c.permission_id)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id != excluding_user_id,
            Permission.codename == ProjectPermission.MEMBERS_MANAGE.value,
        )
    )
    if result.scalar_one() == 0:
        raise LastOwnerError(project_id)

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud import user as user_crud
from app.enums import ProjectRole
from app.exceptions import LastOwnerError, MembershipAlreadyExistsError, MembershipNotFoundError
from app.filters import ProjectFilterParams
from app.models import Project, ProjectMember, User
from app.schemas import ProjectCreate, ProjectMemberRead, ProjectRead
from app.utils import apply_filters, apply_ordering


async def create_project(session: AsyncSession, payload: ProjectCreate, owner: User) -> ProjectRead:
    project = Project(name=payload.name)
    project.members.append(ProjectMember(user=owner, role=ProjectRole.owner))
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
    session: AsyncSession, project_id: int, user_id: int, role: ProjectRole
) -> ProjectMemberRead:
    user = await user_crud.get_user(session, user_id)
    member = ProjectMember(project_id=project_id, user=user, role=role)
    session.add(member)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise MembershipAlreadyExistsError(project_id, user_id)
    return ProjectMemberRead.model_validate(member)


async def update_member_role(
    session: AsyncSession, project_id: int, user_id: int, role: ProjectRole
) -> ProjectMemberRead:
    member = await get_membership(session, project_id, user_id)
    if member is None:
        raise MembershipNotFoundError(project_id, user_id)
    if member.role == ProjectRole.owner and role != ProjectRole.owner:
        await _ensure_not_last_owner(session, project_id, excluding_user_id=user_id)
    member.role = role
    await session.commit()
    await session.refresh(member, attribute_names=["user"])
    return ProjectMemberRead.model_validate(member)


async def remove_member(session: AsyncSession, project_id: int, user_id: int) -> None:
    member = await get_membership(session, project_id, user_id)
    if member is None:
        raise MembershipNotFoundError(project_id, user_id)
    if member.role == ProjectRole.owner:
        await _ensure_not_last_owner(session, project_id, excluding_user_id=user_id)
    await session.delete(member)
    await session.commit()


async def _ensure_not_last_owner(
    session: AsyncSession, project_id: int, excluding_user_id: int
) -> None:
    result = await session.execute(
        select(func.count())
        .select_from(ProjectMember)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.role == ProjectRole.owner,
            ProjectMember.user_id != excluding_user_id,
        )
    )
    if result.scalar_one() == 0:
        raise LastOwnerError(project_id)

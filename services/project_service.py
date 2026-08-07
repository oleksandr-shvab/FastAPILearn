from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from enums import ProjectRole
from exceptions import LastOwnerError, MembershipAlreadyExistsError, MembershipNotFoundError
from filters import ProjectFilter
from models import Project, ProjectMember, User
from schemas import ProjectCreate
from services import user_service


async def create_project(db: AsyncSession, payload: ProjectCreate, owner: User) -> Project:
    project = Project(name=payload.name)
    project.members.append(ProjectMember(user=owner, role=ProjectRole.owner))
    db.add(project)
    await db.commit()
    return project


async def list_projects(db: AsyncSession, filters: ProjectFilter) -> list[Project]:
    query = select(Project).options(
        selectinload(Project.members).selectinload(ProjectMember.user)
    )
    query = filters.sort(filters.filter(query))
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_projects_for_user(
    db: AsyncSession, user_id: int, filters: ProjectFilter
) -> list[Project]:
    query = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user_id)
        .options(selectinload(Project.members).selectinload(ProjectMember.user))
    )
    query = filters.sort(filters.filter(query))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_membership(db: AsyncSession, project_id: int, user_id: int) -> ProjectMember | None:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def list_members(db: AsyncSession, project_id: int) -> list[ProjectMember]:
    result = await db.execute(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .options(selectinload(ProjectMember.user))
    )
    return list(result.scalars().all())


async def add_member(
    db: AsyncSession, project_id: int, user_id: int, role: ProjectRole
) -> ProjectMember:
    user = await user_service.get_user(db, user_id)
    member = ProjectMember(project_id=project_id, user=user, role=role)
    db.add(member)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise MembershipAlreadyExistsError(project_id, user_id)
    return member


async def update_member_role(
    db: AsyncSession, project_id: int, user_id: int, role: ProjectRole
) -> ProjectMember:
    member = await get_membership(db, project_id, user_id)
    if member is None:
        raise MembershipNotFoundError(project_id, user_id)
    if member.role == ProjectRole.owner and role != ProjectRole.owner:
        await _ensure_not_last_owner(db, project_id, excluding_user_id=user_id)
    member.role = role
    await db.commit()
    await db.refresh(member, attribute_names=["user"])
    return member


async def remove_member(db: AsyncSession, project_id: int, user_id: int) -> None:
    member = await get_membership(db, project_id, user_id)
    if member is None:
        raise MembershipNotFoundError(project_id, user_id)
    if member.role == ProjectRole.owner:
        await _ensure_not_last_owner(db, project_id, excluding_user_id=user_id)
    await db.delete(member)
    await db.commit()


async def _ensure_not_last_owner(db: AsyncSession, project_id: int, excluding_user_id: int) -> None:
    result = await db.execute(
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

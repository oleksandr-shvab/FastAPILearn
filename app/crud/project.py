from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import ProjectFilterParams
from app.models import Project
from app.schemas import ProjectCreate, ProjectRead
from app.utils import apply_filters, apply_ordering


async def create_project(
    session: AsyncSession, payload: ProjectCreate, owner_id: int
) -> ProjectRead:
    project = Project(name=payload.name, user_id=owner_id)
    session.add(project)
    await session.commit()
    return ProjectRead.model_validate(project)


async def list_projects(
    session: AsyncSession, filters: ProjectFilterParams
) -> list[ProjectRead]:
    query = apply_filters(select(Project), Project, filters)
    query = apply_ordering(query, Project, filters.order_by)
    result = await session.execute(query)
    return [ProjectRead.model_validate(project) for project in result.scalars().all()]


async def list_projects_for_user(
    session: AsyncSession, user_id: int, filters: ProjectFilterParams
) -> list[ProjectRead]:
    query = apply_filters(select(Project).where(Project.user_id == user_id), Project, filters)
    query = apply_ordering(query, Project, filters.order_by)
    result = await session.execute(query)
    return [ProjectRead.model_validate(project) for project in result.scalars().all()]

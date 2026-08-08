from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import ProjectFilter
from app.models import Project
from app.schemas import ProjectCreate, ProjectRead


async def create_project(
    session: AsyncSession, payload: ProjectCreate, owner_id: int
) -> ProjectRead:
    project = Project(name=payload.name, user_id=owner_id)
    session.add(project)
    await session.commit()
    return ProjectRead.model_validate(project)


async def list_projects(session: AsyncSession, filters: ProjectFilter) -> list[ProjectRead]:
    query = filters.sort(filters.filter(select(Project)))
    result = await session.execute(query)
    return [ProjectRead.model_validate(project) for project in result.scalars().all()]


async def list_projects_for_user(
    session: AsyncSession, user_id: int, filters: ProjectFilter
) -> list[ProjectRead]:
    query = filters.sort(filters.filter(select(Project).where(Project.user_id == user_id)))
    result = await session.execute(query)
    return [ProjectRead.model_validate(project) for project in result.scalars().all()]

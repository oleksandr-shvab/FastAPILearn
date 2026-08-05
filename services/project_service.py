from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from filters import ProjectFilter
from models import Project
from schemas import ProjectCreate


async def create_project(db: AsyncSession, payload: ProjectCreate, owner_id: int) -> Project:
    project = Project(name=payload.name, user_id=owner_id)
    db.add(project)
    await db.commit()
    return project


async def list_projects(db: AsyncSession, filters: ProjectFilter) -> list[Project]:
    query = filters.sort(filters.filter(select(Project)))
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_projects_for_user(
    db: AsyncSession, user_id: int, filters: ProjectFilter
) -> list[Project]:
    query = filters.sort(filters.filter(select(Project).where(Project.user_id == user_id)))
    result = await db.execute(query)
    return list(result.scalars().all())

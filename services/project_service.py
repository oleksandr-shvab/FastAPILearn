from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Project
from schemas import ProjectCreate


async def create_project(db: AsyncSession, payload: ProjectCreate, owner_id: int) -> Project:
    project = Project(name=payload.name, user_id=owner_id)
    db.add(project)
    await db.commit()
    return project


async def list_projects(db: AsyncSession) -> list[Project]:
    result = await db.execute(select(Project))
    return list(result.scalars().all())


async def list_projects_for_user(db: AsyncSession, user_id: int) -> list[Project]:
    result = await db.execute(select(Project).where(Project.user_id == user_id))
    return list(result.scalars().all())

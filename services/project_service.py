from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Project
from schemas import ProjectCreate


async def create_project(db: AsyncSession, payload: ProjectCreate, owner_id: int) -> Project:
    project = Project(name=payload.name, user_id=owner_id)
    db.add(project)
    await db.commit()
    return project


async def list_projects(
    db: AsyncSession, name: str | None = None, user_id: int | None = None
) -> list[Project]:
    query = select(Project)
    if name is not None:
        query = query.where(Project.name.ilike(f"%{name}%"))
    if user_id is not None:
        query = query.where(Project.user_id == user_id)
    result = await db.execute(query)
    return list(result.scalars().all())

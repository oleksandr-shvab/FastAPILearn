from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project
from app.schemas import ProjectRead


async def list_projects(session: AsyncSession) -> list[ProjectRead]:
    query = select(Project)
    result = await session.execute(query)
    return [ProjectRead.model_validate(project) for project in result.scalars().all()]

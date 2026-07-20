from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Project


async def list_projects(db: AsyncSession) -> list[Project]:
    result = await db.execute(select(Project))
    return list(result.scalars().all())

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import RoleNotFoundError
from app.models import Role


async def get_role_by_name(session: AsyncSession, name: str) -> Role:
    result = await session.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    if role is None:
        raise RoleNotFoundError(name)
    return role

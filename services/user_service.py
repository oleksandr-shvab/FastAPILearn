from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from exceptions import UserAlreadyExistsError, UserNotFoundError
from models import Project, User
from schemas import UserCreate


async def create_user_with_project(db: AsyncSession, payload: UserCreate) -> User:
    user = User(username=payload.username, email=payload.email)
    user.projects.append(Project(name=f"{payload.username} Project"))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError(payload.username, payload.email)
    await db.refresh(user, attribute_names=["projects"])
    return user


async def get_user(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.projects))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError(user_id)
    return user


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User))
    return list(result.scalars().all())

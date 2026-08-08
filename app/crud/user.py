from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import security
from app.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.filters import UserFilterParams
from app.models import Project, User
from app.schemas import UserCreate, UserSummary
from app.utils import apply_filters, apply_ordering


async def create_user_with_project(db: AsyncSession, payload: UserCreate) -> User:
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=await security.hash_password(payload.password.get_secret_value()),
    )
    user.projects.append(Project(name=f"{payload.username} Project"))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError(payload.username, payload.email)
    await db.refresh(user, attribute_names=["projects"])
    return user


async def create_superuser(db: AsyncSession, payload: UserCreate) -> User:
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=await security.hash_password(payload.password.get_secret_value()),
        is_admin=True,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError(payload.username, payload.email)
    return user


async def get_user(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.projects))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError(user_id)
    return user


async def list_users(session: AsyncSession, filters: UserFilterParams) -> list[UserSummary]:
    query = apply_filters(select(User), User, filters)
    query = apply_ordering(query, User, filters.order_by)
    result = await session.execute(query)
    return [UserSummary.model_validate(user) for user in result.scalars().all()]


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import security
from exceptions import UserAlreadyExistsError, UserNotFoundError
from filters import UserFilter
from models import Project, User
from schemas import UserCreate

_USERNAME_COLLISION_RETRIES = 3


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


async def list_users(db: AsyncSession, filters: UserFilter) -> list[User]:
    query = filters.sort(filters.filter(select(User)))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_google_id(db: AsyncSession, google_id: str) -> User | None:
    result = await db.execute(
        select(User).where(User.google_id == google_id).options(selectinload(User.projects))
    )
    return result.scalar_one_or_none()


async def get_or_create_google_user(
    db: AsyncSession, google_id: str, email: str, email_verified: bool
) -> User:
    user = await get_user_by_google_id(db, google_id)
    if user is not None:
        return user

    if email_verified:
        result = await db.execute(
            select(User).where(User.email == email).options(selectinload(User.projects))
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.google_id = google_id
            await db.commit()
            await db.refresh(existing, attribute_names=["projects"])
            return existing

    base_username = email.split("@", 1)[0][:50]
    for suffix in ("", *(uuid4().hex[:6] for _ in range(_USERNAME_COLLISION_RETRIES))):
        username = (base_username + suffix)[:50]
        user = User(username=username, email=email, google_id=google_id)
        user.projects.append(Project(name=f"{username} Project"))
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        await db.refresh(user, attribute_names=["projects"])
        return user
    raise UserAlreadyExistsError(base_username, email)

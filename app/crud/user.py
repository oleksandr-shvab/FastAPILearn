from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import security
from app.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.filters import UserFilterParams
from app.models import OAuthAccount, Project, User
from app.schemas import UserCreate, UserSummary
from app.utils import apply_filters, apply_ordering

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


async def list_users(session: AsyncSession, filters: UserFilterParams) -> list[UserSummary]:
    query = apply_filters(select(User), User, filters)
    query = apply_ordering(query, User, filters.order_by)
    result = await session.execute(query)
    return [UserSummary.model_validate(user) for user in result.scalars().all()]


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_oauth_account(
    db: AsyncSession, provider: str, provider_user_id: str
) -> User | None:
    result = await db.execute(
        select(User)
        .join(OAuthAccount)
        .where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
        .options(selectinload(User.projects))
    )
    return result.scalar_one_or_none()


async def get_or_create_oauth_user(
    db: AsyncSession, provider: str, provider_user_id: str, email: str, email_verified: bool
) -> User:
    user = await get_user_by_oauth_account(db, provider, provider_user_id)
    if user is not None:
        return user

    if email_verified:
        result = await db.execute(
            select(User).where(User.email == email).options(selectinload(User.projects))
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.oauth_accounts.append(
                OAuthAccount(provider=provider, provider_user_id=provider_user_id)
            )
            await db.commit()
            await db.refresh(existing, attribute_names=["projects"])
            return existing

    base_username = email.split("@", 1)[0][:50]
    for suffix in ("", *(uuid4().hex[:6] for _ in range(_USERNAME_COLLISION_RETRIES))):
        username = (base_username + suffix)[:50]
        user = User(username=username, email=email)
        user.projects.append(Project(name=f"{username} Project"))
        user.oauth_accounts.append(OAuthAccount(provider=provider, provider_user_id=provider_user_id))
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        await db.refresh(user, attribute_names=["projects"])
        return user
    raise UserAlreadyExistsError(base_username, email)

import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.crud import user as user_crud
from app.exceptions import InvalidCredentialsError, InvalidRefreshTokenError
from app.models import RefreshToken, User

# Need exists to close a timing side-channel that would otherwise let an attacker figure out
# which usernames are registered
_DUMMY_HASH = "$2b$12$2NzijjfzBYx6rTQmzOEYF.xZoKyzXEuw8DqXh2vJ8JlxcMM4s0ULy"


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    user = await user_crud.get_user_by_username(db, username)
    hashed_password = user.hashed_password if user else _DUMMY_HASH
    is_valid = await security.verify_password(password, hashed_password)
    if user is None or not is_valid:
        raise InvalidCredentialsError()
    return user


async def issue_token_pair(db: AsyncSession, user_id: int) -> tuple[str, str]:
    access_token = security.create_access_token(subject=str(user_id))
    refresh_token, jti, expires_at = security.create_refresh_token(subject=str(user_id))
    db.add(RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at))
    await db.commit()
    return access_token, refresh_token


async def rotate_refresh_token(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    try:
        payload = security.decode_refresh_token(refresh_token)
    except (jwt.PyJWTError, ValueError):
        raise InvalidRefreshTokenError()

    result = await db.execute(select(RefreshToken).where(RefreshToken.jti == payload.jti))
    stored = result.scalar_one_or_none()
    if stored is None:
        raise InvalidRefreshTokenError()

    if stored.revoked:
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == stored.user_id)
            .values(revoked=True)
        )
        await db.commit()
        raise InvalidRefreshTokenError()

    stored.revoked = True
    return await issue_token_pair(db, payload.user_id)


async def revoke_refresh_token(db: AsyncSession, refresh_token: str) -> None:
    try:
        payload = security.decode_refresh_token(refresh_token)
    except (jwt.PyJWTError, ValueError):
        return

    result = await db.execute(select(RefreshToken).where(RefreshToken.jti == payload.jti))
    stored = result.scalar_one_or_none()
    if stored is not None:
        stored.revoked = True
        await db.commit()

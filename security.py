from datetime import datetime, timedelta, timezone
from typing import NamedTuple
from uuid import uuid4

import bcrypt
import jwt
from starlette.concurrency import run_in_threadpool

from config import settings

# bcrypt only looks at the first 72 bytes of the input; longer passwords are
# rejected up front instead of being silently truncated.
MAX_PASSWORD_BYTES = 72


def _hash_password_sync(password: str) -> str:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"password must be at most {MAX_PASSWORD_BYTES} bytes")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password_sync(password: str, hashed_password: str) -> bool:
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


async def hash_password(password: str) -> str:
    return await run_in_threadpool(_hash_password_sync, password)


async def verify_password(password: str, hashed_password: str) -> bool:
    return await run_in_threadpool(_verify_password_sync, password, hashed_password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "access":
        raise ValueError("token is not an access token")
    subject = payload.get("sub")
    if subject is None:
        raise ValueError("token is missing the 'sub' claim")
    return int(subject)


class RefreshTokenPayload(NamedTuple):
    user_id: int
    jti: str


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": subject, "type": "refresh", "jti": jti, "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def decode_refresh_token(token: str) -> RefreshTokenPayload:
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != "refresh":
        raise ValueError("token is not a refresh token")
    subject = payload.get("sub")
    jti = payload.get("jti")
    if subject is None or jti is None:
        raise ValueError("token is missing the 'sub' or 'jti' claim")
    return RefreshTokenPayload(user_id=int(subject), jti=jti)

from datetime import datetime, timedelta, timezone

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
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """Decode and verify a JWT, returning the user id encoded in `sub`.

    Raises jwt.PyJWTError (invalid signature, expired, malformed, ...) or
    ValueError (subject missing or isn't a valid user id) on any failure -
    callers map these to a 401 response.
    """
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    subject = payload.get("sub")
    if subject is None:
        raise ValueError("token is missing the 'sub' claim")
    return int(subject)

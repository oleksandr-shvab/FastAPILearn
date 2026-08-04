import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from starlette.concurrency import run_in_threadpool

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

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
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """Decode and verify a JWT, returning the user id encoded in `sub`.

    Raises jwt.PyJWTError (invalid signature, expired, malformed, ...) or
    ValueError (subject isn't a valid user id) on any failure - callers map
    these to a 401 response.
    """
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return int(payload["sub"])

from sqlalchemy.ext.asyncio import AsyncSession

import security
from exceptions import InvalidCredentialsError
from models import User
from services import user_service

# Fixed hash to check the password against when the username doesn't exist,
# so a failed lookup still pays the bcrypt cost and the response time doesn't
# reveal whether the username is registered. Hardcoded rather than computed
# at import time - its value is arbitrary, it just needs to be a real bcrypt
# hash, and hash_password is async now (needs a running event loop to call).
_DUMMY_HASH = "$2b$12$2NzijjfzBYx6rTQmzOEYF.xZoKyzXEuw8DqXh2vJ8JlxcMM4s0ULy"


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    user = await user_service.get_user_by_username(db, username)
    hashed_password = user.hashed_password if user else _DUMMY_HASH
    if user is None or not await security.verify_password(password, hashed_password):
        raise InvalidCredentialsError()
    return user

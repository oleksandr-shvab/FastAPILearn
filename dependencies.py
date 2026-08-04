import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

import security
from database import get_db
from exceptions import UserNotFoundError
from models import User
from services import user_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=401,
        detail="Invalid or missing user identity",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = security.decode_access_token(token)
    except (jwt.PyJWTError, ValueError):
        raise credentials_error
    try:
        return await user_service.get_user(db, user_id)
    except UserNotFoundError:
        raise credentials_error


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

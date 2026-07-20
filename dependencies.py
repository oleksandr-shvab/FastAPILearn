from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from exceptions import UserNotFoundError
from models import User
from services import user_service


async def get_current_user(
    x_user_id: int = Header(..., alias="X-User-Id"),
    db: AsyncSession = Depends(get_db),
) -> User:
    # TEMPORARY: resolves the caller from an X-User-Id header until real
    # authentication (task #3). At that point only this function changes -
    # decode a token/session instead of trusting the header; the routers and
    # require_admin below stay exactly the same.
    try:
        return await user_service.get_user(db, x_user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=401, detail="Invalid or missing user identity")


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user

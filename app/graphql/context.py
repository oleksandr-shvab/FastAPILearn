from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.graphql.loaders import make_member_loader, make_role_loader, make_user_loader
from app.models import User


async def get_graphql_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "db": db,
        "current_user": current_user,
        "member_loader": make_member_loader(db),
        "user_loader": make_user_loader(db),
        "role_loader": make_role_loader(db),
    }

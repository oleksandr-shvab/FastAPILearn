from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.db import get_db
from app.crud import user as user_crud
from app.filters import UserFilter
from app.models import User
from app.schemas import UserRead, UserSummary

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserSummary])
async def list_users(
    filters: UserFilter = FilterDepends(UserFilter),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await user_crud.list_users(db, filters)


@router.get("/me", response_model=UserRead)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
):
    return await user_crud.get_user(db, user_id)

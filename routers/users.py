from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user, require_admin
from models import User
from schemas import UserRead, UserSummary
from services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserSummary])
async def list_users(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    return await user_service.list_users(db)


@router.get("/me", response_model=UserRead)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
):
    return await user_service.get_user(db, user_id)

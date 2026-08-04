from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user, require_admin
from exceptions import UserAlreadyExistsError, UserNotFoundError
from models import User
from schemas import UserCreate, UserRead, UserSummary
from services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=201)
async def create_user_with_project(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await user_service.create_user_with_project(db, payload)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=409, detail="User with this username or email already exists"
        )


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
    try:
        return await user_service.get_user(db, user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")

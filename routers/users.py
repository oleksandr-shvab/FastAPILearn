from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from exceptions import UserAlreadyExistsError, UserNotFoundError
from schemas import UserCreate, UserRead
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


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await user_service.get_user(db, user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")

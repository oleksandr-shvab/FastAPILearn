from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from rate_limit import limiter
from schemas import RefreshTokenRequest, RegisterResponse, Token, UserCreate
from services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
@limiter.limit("3/minute")
async def register(request: Request, payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await user_service.create_user_with_project(db, payload)
    access_token, refresh_token = await auth_service.issue_token_pair(db, user.id)
    return RegisterResponse(user=user, access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.authenticate_user(db, username, password)
    access_token, refresh_token = await auth_service.issue_token_pair(db, user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh(
    request: Request, payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    access_token, refresh_token = await auth_service.rotate_refresh_token(
        db, payload.refresh_token
    )
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
@limiter.limit("10/minute")
async def logout(
    request: Request, payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    await auth_service.revoke_refresh_token(db, payload.refresh_token)

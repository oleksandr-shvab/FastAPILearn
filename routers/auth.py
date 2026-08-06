from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from exceptions import (
    InvalidCredentialsError,
    InvalidGoogleTokenError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
)
from rate_limit import limiter
from schemas import GoogleAuthRequest, RefreshTokenRequest, RegisterResponse, Token, UserCreate
from services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


@router.post("/register", response_model=RegisterResponse, status_code=201)
@limiter.limit("3/minute")
async def register(request: Request, payload: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.create_user_with_project(db, payload)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=409, detail="User with this username or email already exists"
        )
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
    try:
        user = await auth_service.authenticate_user(db, username, password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token, refresh_token = await auth_service.issue_token_pair(db, user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/google", response_class=HTMLResponse, include_in_schema=False)
async def google_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="google_login.html",
        context={"google_client_id": settings.google_client_id},
    )


@router.post("/google", response_model=RegisterResponse)
@limiter.limit("5/minute")
async def google_login(
    request: Request, payload: GoogleAuthRequest, db: AsyncSession = Depends(get_db)
):
    try:
        user = await auth_service.authenticate_google_user(db, payload.id_token)
    except InvalidGoogleTokenError:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    access_token, refresh_token = await auth_service.issue_token_pair(db, user.id)
    return RegisterResponse(user=user, access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh(
    request: Request, payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    try:
        access_token, refresh_token = await auth_service.rotate_refresh_token(
            db, payload.refresh_token
        )
    except InvalidRefreshTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
@limiter.limit("10/minute")
async def logout(
    request: Request, payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    await auth_service.revoke_refresh_token(db, payload.refresh_token)

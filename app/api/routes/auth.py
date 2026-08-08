from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.crud import auth as auth_crud, user as user_crud
from app.schemas import GoogleAuthRequest, RefreshTokenRequest, RegisterResponse, Token, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


@router.post("/register", response_model=RegisterResponse, status_code=201)
@limiter.limit("3/minute")
async def register(request: Request, payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await user_crud.create_user_with_project(db, payload)
    access_token, refresh_token = await auth_crud.issue_token_pair(db, user.id)
    return RegisterResponse(user=user, access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: AsyncSession = Depends(get_db),
):
    user = await auth_crud.authenticate_user(db, username, password)
    access_token, refresh_token = await auth_crud.issue_token_pair(db, user.id)
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
    user = await auth_crud.authenticate_google_user(db, payload.id_token)
    access_token, refresh_token = await auth_crud.issue_token_pair(db, user.id)
    return RegisterResponse(user=user, access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh(
    request: Request, payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    access_token, refresh_token = await auth_crud.rotate_refresh_token(
        db, payload.refresh_token
    )
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
@limiter.limit("10/minute")
async def logout(
    request: Request, payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    await auth_crud.revoke_refresh_token(db, payload.refresh_token)

from typing import Annotated

from authlib.integrations.base_client import OAuthError
from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.oauth import oauth
from app.core.rate_limit import limiter
from app.crud import auth as auth_crud, user as user_crud
from app.exceptions import InvalidGoogleTokenError
from app.schemas import RefreshTokenRequest, RegisterResponse, Token, UserCreate

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


@router.get(
    "/google/login",
    summary="Google login",
    description="Open this URL directly in a browser to start Google sign-in "
    "(redirects to Google's consent screen). Not usable via 'Try it out' - it "
    "isn't a JSON call, it's a browser redirect.",
)
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get(
    "/google/callback",
    name="google_callback",
    include_in_schema=False,  # only reachable via Google's redirect after /google/login
)
@limiter.limit("5/minute")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise InvalidGoogleTokenError()

    userinfo = token.get("userinfo")
    if not userinfo:
        raise InvalidGoogleTokenError()

    user = await auth_crud.authenticate_google_user(db, userinfo)
    access_token, refresh_token = await auth_crud.issue_token_pair(db, user.id)
    return templates.TemplateResponse(
        request=request,
        name="google_auth_result.html",
        context={"access_token": access_token, "refresh_token": refresh_token},
    )


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

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

import security
from database import get_db
from exceptions import InvalidCredentialsError, UserAlreadyExistsError
from rate_limit import limiter
from schemas import RegisterResponse, Token, UserCreate
from services import auth_service, user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
@limiter.limit("3/minute")
async def register(request: Request, payload: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.create_user_with_project(db, payload)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=409, detail="User with this username or email already exists"
        )
    access_token = security.create_access_token(subject=str(user.id))
    return RegisterResponse(user=user, access_token=access_token)


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
    access_token = security.create_access_token(subject=str(user.id))
    return Token(access_token=access_token)

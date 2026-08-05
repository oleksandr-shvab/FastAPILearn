from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user, require_admin
from models import User
from schemas import ProjectCreate, ProjectRead
from services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await project_service.create_project(db, payload, current_user.id)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    name: str | None = None,
    user_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await project_service.list_projects(db, name=name, user_id=user_id)


@router.get("/me", response_model=list[ProjectRead])
async def list_my_projects(
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await project_service.list_projects(db, name=name, user_id=current_user.id)

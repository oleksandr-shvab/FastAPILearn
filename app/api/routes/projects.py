from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.db import get_db
from app.crud import project as project_crud
from app.filters import ProjectFilter
from app.models import User
from app.schemas import ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await project_crud.create_project(db, payload, current_user.id)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    filters: ProjectFilter = FilterDepends(ProjectFilter),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await project_crud.list_projects(db, filters)


@router.get("/me", response_model=list[ProjectRead])
async def list_my_projects(
    filters: ProjectFilter = FilterDepends(ProjectFilter),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await project_crud.list_projects_for_user(db, current_user.id, filters)

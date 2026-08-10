from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin, require_project_permission
from app.core.db import get_db
from app.crud import project as project_crud
from app.enums import ProjectPermission
from app.filters import ProjectFilterParams
from app.models import ProjectMember, User
from app.schemas import (
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberRoleUpdate,
    ProjectRead,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await project_crud.create_project(db, payload, current_user)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    filters: Annotated[ProjectFilterParams, Query()],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await project_crud.list_projects(db, filters)


@router.get("/me", response_model=list[ProjectRead])
async def list_my_projects(
    filters: Annotated[ProjectFilterParams, Query()],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await project_crud.list_projects_for_user(db, current_user.id, filters)


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
async def list_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember = Depends(require_project_permission()),
):
    return await project_crud.list_members(db, project_id)


@router.post("/{project_id}/members", response_model=ProjectMemberRead, status_code=201)
async def add_member(
    project_id: int,
    payload: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember = Depends(require_project_permission(ProjectPermission.MEMBERS_ADD)),
):
    return await project_crud.add_member(db, project_id, payload.user_id, payload.role)


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberRead)
async def update_member_role(
    project_id: int,
    user_id: int,
    payload: ProjectMemberRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember = Depends(require_project_permission(ProjectPermission.MEMBERS_MANAGE)),
):
    return await project_crud.update_member_role(db, project_id, user_id, payload.role)


@router.delete("/{project_id}/members/{user_id}", status_code=204)
async def remove_member(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember = Depends(require_project_permission(ProjectPermission.MEMBERS_MANAGE)),
):
    await project_crud.remove_member(db, project_id, user_id)

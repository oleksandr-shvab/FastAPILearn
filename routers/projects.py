from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user, require_admin, require_project_role
from enums import ProjectRole
from exceptions import LastOwnerError, MembershipAlreadyExistsError, MembershipNotFoundError
from filters import ProjectFilter
from models import ProjectMember, User
from schemas import (
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberRoleUpdate,
    ProjectRead,
)
from services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await project_service.create_project(db, payload, current_user)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    filters: ProjectFilter = FilterDepends(ProjectFilter),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await project_service.list_projects(db, filters)


@router.get("/me", response_model=list[ProjectRead])
async def list_my_projects(
    filters: ProjectFilter = FilterDepends(ProjectFilter),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await project_service.list_projects_for_user(db, current_user.id, filters)


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
async def list_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember = Depends(require_project_role()),
):
    return await project_service.list_members(db, project_id)


@router.post("/{project_id}/members", response_model=ProjectMemberRead, status_code=201)
async def add_member(
    project_id: int,
    payload: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember = Depends(require_project_role(ProjectRole.owner)),
):
    try:
        return await project_service.add_member(db, project_id, payload.user_id, payload.role)
    except MembershipAlreadyExistsError:
        raise HTTPException(status_code=409, detail="User is already a member of this project")


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberRead)
async def update_member_role(
    project_id: int,
    user_id: int,
    payload: ProjectMemberRoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember = Depends(require_project_role(ProjectRole.owner)),
):
    try:
        return await project_service.update_member_role(db, project_id, user_id, payload.role)
    except MembershipNotFoundError:
        raise HTTPException(status_code=404, detail="Membership not found")
    except LastOwnerError:
        raise HTTPException(status_code=409, detail="Cannot demote the last owner")


@router.delete("/{project_id}/members/{user_id}", status_code=204)
async def remove_member(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: ProjectMember = Depends(require_project_role(ProjectRole.owner)),
):
    try:
        await project_service.remove_member(db, project_id, user_id)
    except MembershipNotFoundError:
        raise HTTPException(status_code=404, detail="Membership not found")
    except LastOwnerError:
        raise HTTPException(status_code=409, detail="Cannot remove the last owner")

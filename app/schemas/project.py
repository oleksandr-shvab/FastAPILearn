from pydantic import BaseModel, ConfigDict, Field

from app.enums import ProjectRole


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProjectMemberUser(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberRead(BaseModel):
    user: ProjectMemberUser
    role: ProjectRole

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberCreate(BaseModel):
    user_id: int
    role: ProjectRole = ProjectRole.member


class ProjectMemberRoleUpdate(BaseModel):
    role: ProjectRole


class ProjectRead(ProjectCreate):
    id: int
    members: list[ProjectMemberRead] = []

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ProjectMembershipRead(BaseModel):
    project: ProjectSummary
    role: ProjectRole

    model_config = ConfigDict(from_attributes=True)

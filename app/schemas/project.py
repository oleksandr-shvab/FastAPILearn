from pydantic import BaseModel, ConfigDict, Field

from app.schemas.role import RoleRead


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProjectMemberUser(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberRead(BaseModel):
    user: ProjectMemberUser
    role: RoleRead

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberCreate(BaseModel):
    user_id: int
    role: str = Field("member", min_length=1, max_length=50)


class ProjectMemberRoleUpdate(BaseModel):
    role: str = Field(min_length=1, max_length=50)


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
    role: RoleRead

    model_config = ConfigDict(from_attributes=True)

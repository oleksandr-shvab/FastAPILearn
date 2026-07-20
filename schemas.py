from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str


class ProjectRead(ProjectCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: str
    project: ProjectCreate


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    projects: list[ProjectRead] = []

    model_config = ConfigDict(from_attributes=True)
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProjectRead(ProjectCreate):
    id: int
    user_id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=120)
    password: str = Field(min_length=8, max_length=72)


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    projects: list[ProjectRead] = []

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

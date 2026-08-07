from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, model_validator
from zxcvbn import zxcvbn

from enums import ProjectRole
from security import MAX_PASSWORD_BYTES

_MIN_PASSWORD_SCORE = 2  # zxcvbn scores 0 (weak) - 4 (strong)


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


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=120)
    password: SecretStr = Field(min_length=8, max_length=72)

    @model_validator(mode="after")
    def _check_password_strength(self) -> "UserCreate":
        password = self.password.get_secret_value()
        if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(f"password must be at most {MAX_PASSWORD_BYTES} bytes")
        result = zxcvbn(password, user_inputs=[self.username, self.email])
        if result["score"] < _MIN_PASSWORD_SCORE:
            warning = result["feedback"]["warning"]
            raise ValueError(warning or "password is too weak")
        return self


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool
    project_memberships: list[ProjectMembershipRead] = []

    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterResponse(Token):
    user: UserRead


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class GoogleAuthRequest(BaseModel):
    id_token: str

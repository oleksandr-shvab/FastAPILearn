from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, model_validator
from zxcvbn import zxcvbn

from security import MAX_PASSWORD_BYTES

_MIN_PASSWORD_SCORE = 2  # zxcvbn scores 0 (weak) - 4 (strong)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProjectRead(ProjectCreate):
    id: int
    user_id: int

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


class RegisterResponse(Token):
    user: UserRead

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from wtforms import PasswordField
from wtforms.validators import Optional as OptionalValidator

from app.core import security
from app.core.config import settings
from app.core.db import AsyncSessionLocal, engine
from app.crud import auth as auth_crud, user as user_crud
from app.exceptions import InvalidCredentialsError, UserNotFoundError
from app.models import Project, RefreshToken, User


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]
        async with AsyncSessionLocal() as db:
            try:
                user = await auth_crud.authenticate_user(db, str(username), str(password))
            except InvalidCredentialsError:
                return False
            if not user.is_admin:
                return False
            request.session["user_id"] = user.id
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("user_id")
        if user_id is None:
            return False
        async with AsyncSessionLocal() as db:
            try:
                user = await user_crud.get_user(db, user_id)
            except UserNotFoundError:
                return False
        return user.is_admin


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.is_admin]
    column_details_exclude_list = [User.hashed_password]
    form_columns = [User.username, User.email, User.hashed_password, User.is_admin]
    form_overrides = {"hashed_password": PasswordField}
    form_args = {
        "hashed_password": {"label": "Password", "validators": [OptionalValidator()]}
    }

    async def on_model_change(
        self, data: dict, model: User, is_created: bool, request: Request
    ) -> None:
        password = data.get("hashed_password")
        if password:
            data["hashed_password"] = await security.hash_password(password)
        elif is_created:
            raise ValueError("Password is required when creating a user")
        else:
            data.pop("hashed_password", None)


class ProjectAdmin(ModelView, model=Project):
    column_list = [Project.id, Project.name, Project.owner]
    form_columns = [Project.name, Project.owner]


class RefreshTokenAdmin(ModelView, model=RefreshToken):
    column_list = [
        RefreshToken.id,
        RefreshToken.user,
        RefreshToken.revoked,
        RefreshToken.expires_at,
        RefreshToken.created_at,
    ]
    can_create = False
    form_columns = [RefreshToken.revoked]


def init_admin(app: FastAPI) -> None:
    authentication_backend = AdminAuth(secret_key=settings.jwt_secret_key)
    admin = Admin(app, engine, authentication_backend=authentication_backend)
    admin.add_view(UserAdmin)
    admin.add_view(ProjectAdmin)
    admin.add_view(RefreshTokenAdmin)

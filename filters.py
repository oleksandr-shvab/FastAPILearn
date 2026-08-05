from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import ConfigDict, Field

from models import Project, User


class ProjectFilter(Filter):
    model_config = ConfigDict(populate_by_name=True)

    name__ilike: Optional[str] = Field(default=None, alias="name")
    user_id: Optional[int] = None
    order_by: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = Project


class UserFilter(Filter):
    model_config = ConfigDict(populate_by_name=True)

    username__ilike: Optional[str] = Field(default=None, alias="username")
    email__ilike: Optional[str] = Field(default=None, alias="email")
    is_admin: Optional[bool] = None
    order_by: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = User

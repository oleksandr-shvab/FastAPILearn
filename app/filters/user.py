from typing import Annotated

from pydantic import BaseModel

from app.utils import FilterField, Operator


class UserFilterParams(BaseModel):
    username: Annotated[str | None, FilterField("username")] = None
    username__ilike: Annotated[str | None, FilterField("username", Operator.ILIKE)] = None
    email: Annotated[str | None, FilterField("email")] = None
    email__ilike: Annotated[str | None, FilterField("email", Operator.ILIKE)] = None
    is_admin: Annotated[bool | None, FilterField("is_admin")] = None
    order_by: str | None = None

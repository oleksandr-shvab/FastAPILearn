from typing import Annotated

from pydantic import BaseModel

from app.utils import FilterField, Operator


class ProjectFilterParams(BaseModel):
    name: Annotated[str | None, FilterField("name")] = None
    name__ilike: Annotated[str | None, FilterField("name", Operator.ILIKE)] = None
    user_id: Annotated[int | None, FilterField("user_id")] = None
    order_by: str | None = None

from typing import Annotated

from pydantic import BaseModel

from app.utils import FilterField, Operator


class ProjectFilterParams(BaseModel):
    name: Annotated[str | None, FilterField("name")] = None
    name__ilike: Annotated[str | None, FilterField("name", Operator.ILIKE)] = None
    order_by: str | None = None

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import DeclarativeBase


class Operator(str, Enum):
    EQ = "eq"
    ILIKE = "ilike"


@dataclass(frozen=True)
class FilterField:
    field: str
    operator: Operator = Operator.EQ


def apply_filters(query: Select, model: type[DeclarativeBase], params: BaseModel) -> Select:
    for name, info in type(params).model_fields.items():
        value = getattr(params, name)
        if value is None:
            continue
        filter_field = next((m for m in info.metadata if isinstance(m, FilterField)), None)
        if filter_field is None:
            continue
        column = getattr(model, filter_field.field)
        if filter_field.operator is Operator.ILIKE:
            query = query.where(column.ilike(f"%{value}%"))
        else:
            query = query.where(column == value)
    return query


def apply_ordering(query: Select, model: type[DeclarativeBase], order_by: str | None) -> Select:
    if not order_by:
        return query
    descending = order_by.startswith("-")
    field_name = order_by.removeprefix("-")
    column = getattr(model, field_name, None)
    if column is None:
        return query
    return query.order_by(column.desc() if descending else column.asc())

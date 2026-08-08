from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProjectRead(ProjectCreate):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

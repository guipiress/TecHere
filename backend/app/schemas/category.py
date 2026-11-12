from pydantic import BaseModel, ConfigDict

from backend.app.schemas.common import CategoryName


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: CategoryName


class CategoryResponse(BaseModel):
    id: int
    name: str


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: CategoryName

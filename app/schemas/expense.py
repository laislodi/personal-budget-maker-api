import uuid
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    display_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    display_order: int | None = None


class ItemCreate(BaseModel):
    name: str
    display_order: int = 0


class ItemOverrideUpdate(BaseModel):
    custom_name: str | None = None
    is_hidden: bool | None = None
    display_order: int | None = None


class ItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_order: int
    is_default: bool
    is_hidden: bool
    category_id: uuid.UUID


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_order: int
    is_default: bool
    items: list[ItemResponse]

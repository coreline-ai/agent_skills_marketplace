"""Common schemas."""

from typing import Generic, TypeVar, Any, Optional
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Pagination response model."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    code: Optional[str] = None
    meta: Optional[dict[str, Any]] = None

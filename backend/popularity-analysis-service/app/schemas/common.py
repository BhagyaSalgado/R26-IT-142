from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status: str = Field(default="success")
    message: str
    data: T | None = None


class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    message: str
    details: Any | None = None

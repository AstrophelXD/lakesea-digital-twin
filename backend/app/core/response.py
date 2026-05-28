from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


def success(data: Any = None, message: str = "success") -> dict:
    return {"code": 200, "message": message, "data": data}


def error(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}

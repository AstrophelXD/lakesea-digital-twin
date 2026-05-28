from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int = Field(serialization_alias="pageSize")

    model_config = {"populate_by_name": True}

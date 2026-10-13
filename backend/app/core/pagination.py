import math
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")
MAX_PAGE_SIZE = 100


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(
        default=20, ge=1, le=MAX_PAGE_SIZE, description="Number of elements on a single page"
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


PageParamsDep = Annotated[PageParams, Query()]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=math.ceil(total / params.size),
        )

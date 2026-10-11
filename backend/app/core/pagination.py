"""Reusable pagination models and utilities."""
import math
from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="Page items")
    page: int = Field(1, ge=1, examples=[1], description="Current page number (1-indexed)")
    page_size: int = Field(10, ge=1, le=100, examples=[10], description="Items per page")
    total_items: int = Field(..., examples=[4], description="Total count of items across all pages")
    total_pages: int = Field(..., examples=[1], description="Total number of pages")

    @classmethod
    def create(cls, items: List[T], page: int, page_size: int, total_items: int):
        total_pages = max(1, math.ceil(total_items / max(page_size, 1)))
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

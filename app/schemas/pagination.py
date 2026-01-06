from typing import List, Generic, TypeVar

from fastapi.params import Query
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationResponse(BaseModel, Generic[T]):
    current_page: int = Field(description="current page number")
    size: int = Field(description="size of current page")
    total_page: int = Field(description="total page")
    total_items: int = Field(description="total items size")
    items: List[T] = Field(description="data list")
    # order_by: str | None = Field(default=None, description="get list by")


class PageParams:
    def __init__(self,
                 page: int = Query(1, ge=1, description="page number"),
                 size: int = Query(50, ge=1, le=100, description="size per page"),
                 # order_by: T2 = Query(None, description="get list by")
                 ):
        self.page = page
        self.size = size


class PageParamsWithOrder(PageParams):
    def __init__(self):
        super().__init__()
        raise NotImplementedError()

    pass

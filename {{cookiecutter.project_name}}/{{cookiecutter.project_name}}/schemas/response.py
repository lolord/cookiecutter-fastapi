from typing import Annotated, Generic, List, Optional, TypeVar

from odmantic.bson import BSON_TYPES_ENCODERS
from pydantic import BaseModel, Field, root_validator

# from fastapi import FastAPI, Response, status
# from fastapi.responses import JSONResponse
# https://www.cnblogs.com/alterem/p/11280504.html


class Pagination(BaseModel):
    total: int = 0
    pages: int = 1
    page: int = 1
    page_size: int = 10
    total_count: int = 0

    @root_validator(pre=True)
    def check(cls, values):
        if isinstance(values, BaseModel):
            values = values.model_dump()

        total_count = values.get("total_count", 0)
        page_size = values.get("page_size", 10)
        page = values.get("page", 1)
        total = min(1000, total_count)
        pages = int((total + page_size - 1) / page_size) or 1

        if pages < page:
            pages, page = 1, 1

        values["page"] = page
        values["total"] = total
        values["pages"] = pages

        return values


T = TypeVar("T")


class Resp(BaseModel, Generic[T]):
    code: Annotated[int, Field(description="业务状态码")] = 0
    msg: Optional[Annotated[str, Field(description="错误信息")]] = None
    data: Optional[T] = None

    class Config:
        json_encoders = BSON_TYPES_ENCODERS


class PaginationResp(Resp[List[T]], Generic[T]):
    pagination: Optional[Pagination]

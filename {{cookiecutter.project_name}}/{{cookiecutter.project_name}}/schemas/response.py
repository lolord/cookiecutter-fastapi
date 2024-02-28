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
    code: Annotated[int, Field(description="业务状态码")] = 0
    pagination: Optional[Pagination]


# 200 OK - [GET]：服务器成功返回用户请求的数据，该操作是幂等的（Idempotent）。
# 201 CREATED - [POST/PUT/PATCH]：用户新建或修改数据成功。
# 202 Accepted - [*]：表示一个请求已经进入后台排队（异步任务）
# 204 NO CONTENT - [DELETE]：用户删除数据成功。
# 400 INVALID REQUEST - [POST/PUT/PATCH]：用户发出的请求有错误，服务器没有进行新建或修改数据的操作，该操作是幂等的。
# 401 Unauthorized - [*]：表示用户没有权限（令牌、用户名、密码错误）。
# 403 Forbidden - [*] 表示用户得到授权（与401错误相对），但是访问是被禁止的。
# 404 NOT FOUND - [*]：用户发出的请求针对的是不存在的记录，服务器没有进行操作，该操作是幂等的。
# 406 Not Acceptable - [GET]：用户请求的格式不可得（比如用户请求JSON格式，但是只有XML格式）。
# 410 Gone -[GET]：用户请求的资源被永久删除，且不会再得到的。
# 422 Unprocesable entity - [POST/PUT/PATCH] 当创建一个对象时，发生一个验证错误。
# 500 INTERNAL SERVER ERROR - [*]：服务器发生错误，用户将无法判断发出的请求是否成功。

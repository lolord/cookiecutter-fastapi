from enum import Enum
from typing import Annotated, Any, Generic, List, Optional, TypeVar

from odmantic.bson import BSON_TYPES_ENCODERS
from pydantic import BaseModel, Field, model_validator


class APIState(Enum):
    OK = 0
    # Business error code
    FORMAT_INVALID = 1000  # 格式错误
    DATA_NOT_FOUND = 2001  # 数据不存在
    DATA_DELETED = 2002  # 数据已删除
    DATA_EXISTED = 2003  # 数据已存在
    DATA_INVALID = 2004  # 数据无效
    LOGIN_FAILED = 3000  # 登录失败
    OPERATE_INVALID = 4000  # 无效操作
    PERMISSION_DENIED = 5000  # 权限不足
    API_TIMEOUT = 6000
    QUERY_TIMEOUT = 6001
    OTHER = 10000


# openapi doc
APIState.__doc__ = "<br/>".join(f"{i.value}:{i.name}" for i in APIState)


T = TypeVar("T")


class Resp(BaseModel, Generic[T]):
    code: Annotated[APIState, Field(description="业务状态码")] = APIState.OK
    msg: Optional[Annotated[str, Field(description="错误信息")]] = None
    data: T
    model_config = {"json_encoders": BSON_TYPES_ENCODERS}


class Pagination(BaseModel):
    total: Annotated[int, Field(description="允许查询最大结果数量")] = 0
    pages: Annotated[int, Field(description="总分数")] = 1
    page: Annotated[int, Field(description="当前页码")] = 1
    page_size: Annotated[int, Field(description="分页大小")] = 10
    total_count: Annotated[int, Field(description="查询结果数量")] = 0

    @model_validator(mode="before")
    def check(cls, values: dict[str, Any]) -> dict[str, Any]:
        total_count = values.get("total_count", 0)
        page_size = values.get("page_size", 10)
        page = values.get("page", 1)
        total = min(1000, total_count)
        pages = int((total + page_size - 1) / page_size) or 1

        values["page"] = page
        values["total"] = total
        values["pages"] = pages

        return values


class PageResp(Resp, Generic[T]):
    data: Annotated[List[T], Field(description="数据集")] = []
    pagination: Annotated[Pagination, Field(description="分页")]

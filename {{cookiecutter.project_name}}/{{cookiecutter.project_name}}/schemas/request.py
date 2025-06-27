from typing import List, Optional

from pydantic import BaseModel, Field


class PaginationQuery(BaseModel):
    page: int = 1
    page_size: int = 10

    sort_by: Optional[str] = None
    sort_order: str = "ascend"

    q: Optional[str] = Field(None, description="查询对象")
    keys: List[str] = Field([], description="查询字段")

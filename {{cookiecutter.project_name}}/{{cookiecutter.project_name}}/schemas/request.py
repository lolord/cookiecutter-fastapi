from typing import Optional

from pydantic import BaseModel


class PaginationQuery(BaseModel):
    page: int = 1
    page_size: int = 10

    sort_by: Optional[str] = None
    sort_order: str = "ascend"

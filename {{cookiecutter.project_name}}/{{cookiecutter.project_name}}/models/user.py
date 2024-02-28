from datetime import datetime
from typing import List, Optional, TypeAlias

from odmantic import Field, Index, Model, ObjectId
from odmantic.query import asc
from pydantic import EmailStr
from rbac.model import PermissionName, RoleName

UserID: TypeAlias = ObjectId


class User(Model):
    email: EmailStr = Field(...)
    nickname: str = Field(..., min_length=1, max_length=32)
    hashed_password: str = Field("", max_length=128)
    enabled: bool = True
    deleted: int = 0
    roles: List[RoleName] = []
    permissions: List[PermissionName] = []

    u_at: datetime = Field(description="修改时间", default_factory=datetime.now)

    c_at: datetime = Field(description="创建时间", default_factory=datetime.now)

    expire_at: Optional[datetime] = Field(default=None, description="失效时间")

    model_config = {
        "collection": "user",
        "parse_doc_with_default_factories": True,
        "indexes": lambda: [
            Index(User.email, unique=True),
            Index(User.nickname),
            Index(asc(User.c_at)),
        ],
    }


class SimpleUser(Model):
    email: EmailStr = Field(...)
    nickname: str = Field(..., min_length=3, max_length=14)
    enabled: bool = True
    roles: List[RoleName] = []

    model_config = {"collection": "user"}


# engine = AIOEngine()
# await engine.configure_database([User])

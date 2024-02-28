from datetime import datetime
from typing import List, Optional, TypeAlias

from odmantic import Field, Model, ObjectId

RoleID: TypeAlias = ObjectId
RoleName: TypeAlias = str
PermissionID: TypeAlias = ObjectId
PermissionName: TypeAlias = str


class SYSTEAM_ROLES:
    ANONYMOUS = "anonymous"
    ALL_USER = "user"
    ADMIN = "admin"


class Role(Model):
    name: str = Field(..., unique=True, min_length=1, max_length=128)
    description: str = ""
    permissions: List[PermissionName] = []
    enabled: bool = True

    model_config = {"collection": "role"}


class Permission(Model):
    name: PermissionName
    description: str = ""
    creator: Optional[ObjectId] = Field(default=None, description="创建人")
    expire_at: Optional[datetime] = Field(default=None, description="失效时间")

    model_config = {"collection": "permission"}


class RBACRoute(Model):
    path: str
    name: str
    method: str = Field(..., min_length=1, max_length=100)
    endpoint: str = "endpoint function name"
    tags: List[str] = []
    description: str = ""
    deprecated: bool = False
    permissions: List[PermissionName] = []

    model_config = {"collection": "rbac_route"}


class Menu(Model):
    path: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    enabled: bool = True
    permissions: List[PermissionName] = Field([])

    model_config = {"collection": "menu", "parse_doc_with_default_factories": True}

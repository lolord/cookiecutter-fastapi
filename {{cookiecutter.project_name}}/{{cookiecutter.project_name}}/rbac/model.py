from datetime import datetime
from typing import Annotated, Iterable, List, Optional, Set, TypeAlias, TypeVar

from odmantic import Field, Model, ObjectId, WithBsonSerializer
from odmantic.config import ODMConfigDict
from pydantic import PlainSerializer, StringConstraints

RoleID: TypeAlias = ObjectId
RoleName: TypeAlias = str
PermissionID: TypeAlias = ObjectId
PermissionName: TypeAlias = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, min_length=1, max_length=128, pattern=r"^\S+$"),
]

_T = TypeVar("_T")


def frozenset_serializer(v: Iterable[_T]) -> list[_T]:
    arr = list(v)
    arr.sort()
    return arr


PermissionNames: TypeAlias = Annotated[
    Set[PermissionName],
    # Bson serializer is not require
    WithBsonSerializer(frozenset_serializer),
    PlainSerializer(frozenset_serializer, return_type=List[str]),
]

RoleNames: TypeAlias = Annotated[
    Set[RoleName],
    WithBsonSerializer(frozenset_serializer),
    PlainSerializer(frozenset_serializer, return_type=List[str]),
]


class SYSTEAM_ROLES:
    ANONYMOUS = "anonymous"
    ALL_USER = "user"
    ADMIN = "admin"


class Role(Model):
    name: str = Field(..., unique=True, min_length=1, max_length=128)
    description: str = ""
    permissions: PermissionNames = Field([])
    enabled: bool = True

    model_config = ODMConfigDict({"collection": "role"})


class Permission(Model):
    name: PermissionName
    description: str = ""
    creator: Optional[ObjectId] = Field(default=None, description="创建人")
    expire_at: Optional[datetime] = Field(description="失效时间", default_factory=datetime.now)

    model_config = ODMConfigDict({"collection": "permission"})


class RBACRoute(Model):
    path: str
    name: str
    method: str = Field(..., min_length=1, max_length=100)
    endpoint: str = Field(..., description="endpoint function name")
    tags: List[str] = []
    description: str = ""
    deprecated: bool = False
    permissions: PermissionNames = Field([])

    model_config = ODMConfigDict({"collection": "rbac_route"})


class Menu(Model):
    path: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    enabled: bool = True
    permissions: PermissionNames = Field([])

    model_config = ODMConfigDict({"collection": "menu", "parse_doc_with_default_factories": True})

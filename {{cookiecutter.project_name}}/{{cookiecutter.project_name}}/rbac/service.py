import asyncio
from typing import List, Optional

from odmantic import ObjectId
from odmantic.query import in_
from pydantic import BaseModel

from {{cookiecutter.project_name}}.api.user import SimpleUser
from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import User
from {{cookiecutter.project_name}}.schemas.errors import DataNotFoundError, PermissionDeniedError

from .model import Permission, Role, RoleID


class RoleProfile(BaseModel):
    id: RoleID
    name: str
    description: str
    permissions: List[Permission] = []
    users: List[SimpleUser] = []
    enabled: bool


async def get_role(id: str | ObjectId) -> Optional[Role]:
    return await engine.find_one(Role, Role.id == id)


async def get_role_profile(id: RoleID) -> RoleProfile:
    role = await get_role(id)
    if role is None:
        raise DataNotFoundError(f"Role(id={id})")
    users_fut = asyncio.ensure_future(engine.find(SimpleUser, {"roles": id}))
    permissions_fut = asyncio.ensure_future(engine.find(Permission, in_(Permission.name, role.permissions)))

    users = await users_fut
    permissions = await permissions_fut
    return RoleProfile(
        id=role.id,
        name=role.name,
        description=role.description,
        enabled=role.enabled,
        users=users,
        permissions=permissions,
    )


async def remove_role(id: RoleID) -> None:
    role = await engine.must_find_one(Role, id=id)
    if role.name == "admin":
        raise PermissionDeniedError(msg="delete admin")
    await engine.get_collection(User).update_many({"roles": role.name}, {"$pull": {"roles": role.name}})
    await engine.delete(role)

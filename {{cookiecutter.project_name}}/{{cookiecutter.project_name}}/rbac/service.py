import asyncio
from typing import List, Optional, cast

from fastapi import Query
from odmantic import ObjectId
from odmantic.query import in_
from pydantic import BaseModel
from starlette.requests import Request

from {{cookiecutter.project_name}}.api.user import SimpleUser, User
from {{cookiecutter.project_name}}.db import engine

from .model import Permission, Role, RoleID


class RoleProfile(BaseModel):
    id: RoleID
    name: str
    description: str
    permissions: List[Permission] = []
    users: List[SimpleUser] = []
    enabled: bool


async def get_role_profile(id: RoleID) -> RoleProfile:
    role = await engine.find_one(Role, Role.id == id)
    if role is None:
        raise ValueError(f"Role not find: {id}")
    users_fut = asyncio.ensure_future(engine.find(SimpleUser, {"roles": id}))
    permissions_fut = asyncio.ensure_future(
        engine.find(Permission, in_(Permission.name, role.permissions))
    )

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


async def get_role(
    role_id: Optional[str] = Query(None),
    role_name: Optional[str] = Query(None),
) -> Optional[Role]:
    if role_id:
        return await engine.find_one(Role, Role.id == ObjectId(role_id))
    if role_name:
        return await engine.find_one(Role, Role.name == role_name)
    return None


async def get_request_user(request: Request) -> Optional[User]:
    return cast(Optional[User], getattr(request.state, "user", None))

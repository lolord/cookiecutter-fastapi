import asyncio
from typing import List, Optional, cast

from api.user import SimpleUser, User
from db import engine
from extends.logger import logger
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute, APIRouter, Mount
from odmantic import ObjectId
from odmantic.query import in_
from pydantic import BaseModel
from services.security import credentials_exception, not_enough_permissions
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from .model import Permission, RBACRoute, Role, RoleID


async def update_rbac_routes(app: FastAPI):
    await engine.database[+RBACRoute].update_many({}, {"$set": {"deprecated": True}})

    for route in app.routes:
        if isinstance(route, Mount):
            continue
        route = cast(APIRoute, route)
        logger.info(route.path)
        logger.info(getattr(route, "dependencies", None))
        # permissions = []
        # depends: ParamsDepends
        # for depends in getattr(route, "dependencies", []):
        #     if depends.dependency is jwt_required:
        #         permissions.append("login")

        tags = []
        for tag in getattr(route, "tags", []):
            if tag not in tags:
                tags.append(tag)

        name = getattr(route, "name", "")
        for method in getattr(route, "methods", []):
            if method:
                await engine.database[+RBACRoute].update_one(
                    {"method": method, "path": route.path},
                    {
                        "$set": {"deprecated": False, "tags": tags, "name": name},
                        # "$addToSet": {"permissions": {"$each": permissions}},
                    },
                    upsert=True,
                )

    permissions = [
        Permission(name="admin", description="管理员权限"),  # type: ignore
        Permission(name="user", description="普通用户权限"),  # type: ignore
    ]

    for i in permissions:
        if await engine.count(Permission, Permission.name == i.name) == 0:
            await engine.save(i)

    roles = [
        Role(name="admin", description="管理员", permissions=["admin"]),  # type: ignore
        Role(name="user", description="普通用户员", permissions=["user"]),  # type: ignore
    ]
    for i in roles:
        if await engine.count(Role, Role.name == i.name) == 0:
            await engine.save(i)


# NOTE: Using middleware will traverse the route once more
class RBACMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

        while True:
            if isinstance(app, APIRouter):
                break
            elif hasattr(app, "app"):
                app = getattr(app, "app")
            else:
                raise ValueError
        self.routes = []
        for route in app.routes:
            if not isinstance(route, Mount):
                self.routes.append(route)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            await self.matches(request)
        except HTTPException as e:
            return JSONResponse(
                jsonable_encoder({"detail": e.detail}), status_code=e.status_code
            )
        response = await call_next(request)
        return response

    async def matches(self, request: Request):
        if request.scope["type"] != "http":
            return
        method = request.scope["method"]
        matched: Optional[APIRoute] = None

        for route in self.routes:
            if (
                route.methods
                and method in route.methods
                and route.path_regex.match(request.scope["path"])
            ):
                matched = route
                break

        if matched is None:
            return

        route = await engine.find_one(
            RBACRoute, RBACRoute.method == method, RBACRoute.path == matched.path
        )
        user = cast(Optional[User], request.scope["user"])

        if route and route.permissions:
            if user is None:
                raise credentials_exception

            user.permissions.add("login")
            if not (set(route.permissions) & set(user.permissions)):
                raise not_enough_permissions


# rbac_middleware = Middleware(RBACMiddleware)


class RoleProfile(BaseModel):
    id: RoleID
    name: str
    description: str
    permissions: List[Permission] = []
    users: List[SimpleUser] = []
    enabled: bool


async def get_role_profile(id: RoleID):
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


async def get_request_user(request: Request):
    return cast(User, request.scope.get("user"))

from typing import Optional, cast

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler
from fastapi.routing import APIRoute, APIRouter, Mount
from odmantic.query import eq, in_
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import User
from {{cookiecutter.project_name}}.services.security import credentials_exception, get_request_user, not_enough_permissions
from {{cookiecutter.project_name}}.settings import settings

from .model import Permission, PermissionNames, RBACRoute, Role


async def get_user_permissions(
    user: User,
) -> PermissionNames:
    permissions = set()
    if user.roles:
        async for role in engine.find(
            Role,
            in_(Role.name, user.roles),
            eq(Role.enabled, True),
        ):
            permissions.update(role.permissions)
    return permissions


class RBACMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

        while True:
            if isinstance(app, APIRouter):
                break
            if hasattr(app, "app"):
                app = getattr(app, "app")

        self.routes = []
        for route in app.routes:
            if not isinstance(route, Mount):
                self.routes.append(route)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            await self.matches(request)
        except StarletteHTTPException as e:
            return await http_exception_handler(request, e)
        return await call_next(request)

    async def matches(self, request: Request) -> None:
        if request.scope["type"] != "http":  # pragma: no cover
            return

        # if (
        #     request.url.path.endswith("/auth/register")
        #     or request.url.path.endswith("/auth/login")
        #     or request.url.path.endswith("/auth/user-exists")
        #     or request.url.path.endswith("/docs")
        #     or request.url.path.endswith("/docsx")
        #     or "/publics" in request.url.path
        # ):
        #     return

        method = request.scope["method"]
        matched: Optional[APIRoute] = None

        for _route in self.routes:
            api_route = cast(APIRoute, _route)
            if api_route.methods and method in api_route.methods and api_route.path_regex.match(request.scope["path"]):
                matched = api_route
                break

        if matched is None:
            # 没有匹配到路由, FastAPI 将抛出 HTTPException
            return

        route = await engine.find_one(RBACRoute, RBACRoute.method == method, RBACRoute.path == matched.path)
        assert route, "must find RBACRoute"
        if not route.permissions:
            return
        user = await get_request_user(request)
        if not user:
            raise credentials_exception

        user.permissions = await get_user_permissions(user)
        if "admin" in user.permissions:
            return
        if not (set(route.permissions) & set(user.permissions)):
            raise not_enough_permissions

    @staticmethod
    async def update_rbac_routes(app: FastAPI) -> None:
        await engine.database[+RBACRoute].update_many({}, {"$set": {"deprecated": True}})
        for route in app.routes:
            if isinstance(route, Mount):
                continue
            route = cast(APIRoute, route)

            tags = []
            for tag in getattr(route, "tags", []):
                if tag not in tags:
                    tags.append(tag)

            name = getattr(route, "name", "")
            for method in getattr(route, "methods", []):
                if method:
                    update = {
                        "$set": {
                            "deprecated": False,
                            "tags": tags,
                            "name": name,
                            "endpoint": route.endpoint.__name__,
                        }
                    }
                    if route.path.startswith(settings.API_VER + "/rbac"):
                        update["$addToSet"] = {"permissions": "admin"}
                    await engine.database[+RBACRoute].update_one(
                        {"method": method, "path": route.path}, update, upsert=True
                    )

        permissions = [
            Permission(name="admin", description="管理员权限"),  # type: ignore
            Permission(name="user", description="普通用户权限"),  # type: ignore
        ]

        for p in permissions:
            await engine.upsert_one(p, Permission.name == p.name)

        roles = [
            Role(name="admin", description="管理员", permissions=["admin"]),  # type: ignore
            Role(name="user", description="普通用户", permissions=["user"]),  # type: ignore
        ]
        for r in roles:
            await engine.upsert_one(r, Role.name == r.name)

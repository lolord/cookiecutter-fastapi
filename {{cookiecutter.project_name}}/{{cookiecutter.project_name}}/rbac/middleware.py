from typing import Optional, cast

from fastapi import FastAPI
from fastapi.routing import APIRoute, APIRouter, Mount
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.services.security import (
    credentials_exception,
    not_enough_permissions,
)

from .model import Permission, RBACRoute, Role
from .service import get_request_user


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
        await self.matches(request)
        response = await call_next(request)
        return response

    async def matches(self, request: Request):
        if request.scope["type"] != "http":
            return
        method = request.scope["method"]
        matched: Optional[APIRoute] = None

        api_route: APIRoute
        for api_route in self.routes:
            if (
                api_route.methods
                and method in api_route.methods
                and api_route.path_regex.match(request.scope["path"])
            ):
                matched = api_route
                break

        if matched is None:
            return

        route = await engine.find_one(
            RBACRoute, RBACRoute.method == method, RBACRoute.path == matched.path
        )
        user = await get_request_user(request)
        if route and route.permissions:
            if user is None:
                raise credentials_exception

            user.permissions.add("login")
            if not (set(route.permissions) & set(user.permissions)):
                raise not_enough_permissions

    @staticmethod
    async def update_rbac_routes(app: FastAPI):
        await engine.database[+RBACRoute].update_many(
            {}, {"$set": {"deprecated": True}}
        )

        for route in app.routes:
            if isinstance(route, Mount):
                continue
            route = cast(APIRoute, route)

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
                            "$set": {
                                "deprecated": False,
                                "tags": tags,
                                "name": name,
                                "endpoint": route.endpoint.__name__,
                            },
                            # "$addToSet": {"permissions": {"$each": permissions}},
                        },
                        upsert=True,
                    )

        permissions = [
            Permission(name="admin", description="管理员权限"),  # type: ignore
            Permission(name="user", description="普通用户权限"),  # type: ignore
        ]

        for i in permissions:
            await engine.upsert(i)

        roles = [
            Role(name="admin", description="管理员", permissions=["admin"]),  # type: ignore
            Role(name="user", description="普通用户", permissions=["user"]),  # type: ignore
        ]
        for i in roles:
            await engine.upsert(i)

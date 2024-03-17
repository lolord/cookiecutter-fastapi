from typing import Annotated, Optional

from api.user import User
from db import engine
from fastapi import APIRouter, Body, Depends, Path, Query
from odmantic import ObjectId
from odmantic.query import in_
from pydantic import BaseModel, Field, constr
from schemas import PaginationQuery, PaginationResp, Resp

from .model import (
    Menu,
    Permission,
    PermissionName,
    PermissionNames,
    RBACRoute,
    Role,
    RoleID,
)
from .service import RoleProfile, get_request_user, get_role_profile

router = APIRouter(
    prefix="/rbac",
    tags=["Role-Based Access Control"],
)


class RoleQuery(PaginationQuery):
    id: Optional[RoleID] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None
    permissions: Optional[PermissionName] = None


@router.get(
    "/roles",
    summary="管理员获取角色列表",
    response_model=PaginationResp[Role],
)
async def get_roles(
    query: RoleQuery = Depends(),
):
    return await engine.find_pagination(Role, query)


@router.get("/roles/{id}", summary="角色信息", response_model=Resp[RoleProfile])
async def get_role(id: RoleID = Path(...)):
    return Resp(data=get_role_profile(id=id))


@router.post("/roles", summary="创建角色")
async def post_role(role: Role = Body(...)) -> Resp[Role]:
    exists = await engine.count(Role, Role.name == role.name)
    if exists:
        raise ValueError(f"role: {role.name} already exists")

    await engine.save(role)
    return Resp(data=role)


@router.put("/roles", summary="编辑角色信息")
async def edit_roles(role: Role = Body(...)) -> Resp[Role]:
    exists = await engine.exists(Role, Role.id == role.id)
    if not exists:
        return Resp(code=400, msg="role does not exist.")
    if role.name == "admin":
        return Resp(code=400, msg="Not enough permissions.")
    role = await engine.save(role)
    return Resp(data=role)


@router.delete(
    "/roles/{id}",
    summary="删除角色",
    response_model=Resp[bool],
)
async def delete_roles(
    id: RoleID = Path(...), force: bool = Query(False, description="强制删除")
):
    role = await engine.find_one(Role, Role.id == id)
    if not role:
        return Resp(code=400, msg="role does not exist.")
    if role.name == "admin":
        return Resp(code=400, msg="admin cannot be deleted.")

    users = await engine.find(User, User.roles == id)
    if users and not force:
        return Resp(code=400, msg="role member is not empty.")
    else:
        for user in users:
            user.roles.remove(role.name)
        await engine.save_all(users)
    await engine.delete(role)
    return Resp(data=True)


@router.get(
    "/routes",
    summary="路由列表",
    response_model=PaginationResp[RBACRoute],
)
async def get_routes(query: PaginationQuery = Depends()):
    if not query.sort_by:
        query.sort_by = str(RBACRoute.tags)
    return await engine.find_pagination(
        RBACRoute, query, {+RBACRoute.deprecated: False}
    )


async def validate_route(id: ObjectId = Path(...)):
    route = await engine.find_one(RBACRoute, RBACRoute.id == id)
    if not route:
        raise ValueError(f"RBACRoute(id={id}) does not exist")

    return route


@router.post(
    "/routes/{id}/permissions",
    summary="添加路由权限",
    response_model=Resp[RBACRoute],
)
async def post_route_permission(
    route: RBACRoute = Depends(validate_route),
    permission: Annotated[str, constr(strip_whitespace=True, to_lower=True)] = Body(
        ...
    ),
    user: User = Depends(get_request_user),
):
    if permission in route.permissions:
        raise ValueError(f"{permission} already exists")

    route.permissions.add(permission)
    await engine.save(route)
    if await engine.find(Permission, in_(Permission.id, list(permission))) == 0:
        await engine.save(Permission(name=permission, creator=user.id))  # type: ignore

    return Resp(data=route)


@router.delete(
    "/routes/{id}/permissions",
    summary="删除路由权限",
    response_model=Resp[RBACRoute],
)
async def delete_route_permission(
    route: RBACRoute = Depends(validate_route),
    permission: Annotated[str, constr(strip_whitespace=True, to_lower=True)] = Body(
        ...
    ),
):
    if permission not in route.permissions:
        raise ValueError(f"{permission} does not exist")

    route.permissions.remove(permission)
    await engine.save(route)
    return Resp(data=route)


@router.get("/menus", summary="菜单列表", response_model=PaginationResp[Menu])
async def get_menu(query: PaginationQuery = Depends()):
    if not query.sort_by:
        query.sort_by = str(Menu.path)
    return await engine.find_pagination(Menu, query)


class MenuPost(BaseModel):
    path: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    enabled: bool = True
    permissions: PermissionNames = Field([])


@router.post("/menus", summary="新增菜单", response_model=Menu)
async def post_menu(menu: MenuPost = Depends()):
    return await engine.save(Menu(**menu.model_dump()))


async def validate_menu(mid: str = Path(...)):
    menu = await engine.find_one(Menu, Menu.id == mid)
    if not menu:
        raise ValueError(f"Not find Menu({mid})")
    return menu


@router.put("/menus/{mid}", summary="修改菜单", response_model=Menu)
async def put_menu(menu: Menu = Depends(validate_menu)):
    return await engine.save(menu)


@router.delete("/menus/{mid}", summary="删除菜单", response_model=None)
async def delete_menu(menu: Menu = Depends(validate_menu)):
    await engine.delete(menu)

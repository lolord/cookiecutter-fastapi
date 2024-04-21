from typing import Annotated, Optional, cast

from fastapi import APIRouter, Body, Depends, Path, Query
from odmantic import ObjectId
from odmantic.field import FieldProxy
from odmantic.query import in_
from pydantic import BaseModel, Field, constr

from {{cookiecutter.project_name}}.api.user import User
from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.schemas import APIState, PageResp, PaginationQuery, Resp

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
)
async def get_roles(
    query: RoleQuery = Depends(),
) -> PageResp[Role]:
    return await engine.find_pagination(Role, query)


@router.get("/roles/{id}", summary="角色信息")
async def get_role(id: RoleID = Path(...)) -> Resp[RoleProfile]:
    return Resp(data=await get_role_profile(id=id))


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
        return Resp(code=APIState.DATA_NOT_FOUND, msg="role does not exist.")
    if role.name == "admin":
        return Resp(code=APIState.PERMISSION_DENIED, msg="Not enough permissions.")
    role = await engine.save(role)
    return Resp(data=role)


@router.delete(
    "/roles/{id}",
    summary="删除角色",
)
async def delete_roles(
    id: RoleID = Path(...), force: bool = Query(False, description="强制删除")
) -> Resp[None]:
    role = await engine.find_one(Role, Role.id == id)
    if not role:
        return Resp(code=APIState.DATA_EXISTED, msg="role does not exist.")
    if role.name == "admin":
        return Resp(code=APIState.DATA_DELETED, msg="admin cannot be deleted.")

    users = await engine.find(User, User.roles == id)
    if users and not force:
        return Resp(code=APIState.OPERATE_INVALID, msg="role member is not empty.")
    else:
        for user in users:
            user.roles.remove(role.name)
        await engine.save_all(users)
    await engine.delete(role)
    return Resp()


@router.get(
    "/routes",
    summary="路由列表",
)
async def get_routes(query: PaginationQuery = Depends()) -> PageResp[RBACRoute]:
    if not query.sort_by:
        query.sort_by = +cast(FieldProxy, RBACRoute.tags)
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
)
async def post_route_permission(
    route: RBACRoute = Depends(validate_route),
    permission: Annotated[str, constr(strip_whitespace=True, to_lower=True)] = Body(
        ...
    ),
    user: User = Depends(get_request_user),
) -> Resp[RBACRoute]:
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
)
async def delete_route_permission(
    route: RBACRoute = Depends(validate_route),
    permission: Annotated[str, constr(strip_whitespace=True, to_lower=True)] = Body(
        ...
    ),
) -> Resp[RBACRoute]:
    if permission not in route.permissions:
        raise ValueError(f"{permission} does not exist")

    route.permissions.remove(permission)
    await engine.save(route)
    return Resp(data=route)


@router.get("/menus", summary="菜单列表")
async def get_menu(query: PaginationQuery = Depends()) -> PageResp[Menu]:
    if not query.sort_by:
        query.sort_by = str(Menu.path)
    return await engine.find_pagination(Menu, query)


class MenuPost(BaseModel):
    path: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    enabled: bool = True
    permissions: PermissionNames = Field([])


@router.post("/menus", summary="新增菜单")
async def post_menu(post: MenuPost = Depends()) -> Resp[Menu]:
    menu = Menu(**post.model_dump())
    await engine.save(menu)
    return Resp(data=menu)


@router.put("/menus", summary="修改菜单", response_model=Menu)
async def put_menu(menu: Menu = Depends()):
    return await engine.save(menu)


@router.delete("/menus/{mid}", summary="删除菜单")
async def delete_menu(mid: ObjectId = Path(...)) -> Resp[None]:
    menu = await engine.find_one(Menu, Menu.id == mid)
    if not menu:
        return Resp(code=APIState.DATA_NOT_FOUND, msg=f"Not find Menu({mid})")
    await engine.delete(menu)
    return Resp()

"""Role-Based Access Control

The RBACMiddleware will take over routing access permissions
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, Path
from odmantic import ObjectId
from pydantic import BaseModel, Field

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.schemas import (
    APIState,
    PageResp,
    PaginationQuery,
    Resp,
    errors,
)
from {{cookiecutter.project_name}}.schemas.errors import APIError
from {{cookiecutter.project_name}}.services.security import RequestUser

from .model import (
    Menu,
    Permission,
    PermissionName,
    PermissionNames,
    RBACRoute,
    Role,
    RoleID,
)
from .service import RoleProfile, get_role_profile, remove_role

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
    name="rbac:roles",
)
async def get_roles(
    query: RoleQuery = Depends(),
) -> PageResp[Role]:
    return await engine.find_pagination(Role, query)


@router.get(
    "/roles/{id}",
    summary="角色信息",
    name="rbac:role-profile",
)
async def get_role(id: RoleID = Path(...)) -> Resp[RoleProfile]:
    return Resp(data=await get_role_profile(id=id))


@router.post("/roles", summary="创建角色", name="rbac:roles")
async def post_role(role: Role = Body(...)) -> Resp[Role]:
    exists = await engine.count(Role, Role.name == role.name)
    if exists:
        raise errors.DataExistedError(f"Role(name={role.name})")

    await engine.save(role)
    return Resp(data=role)


@router.put("/roles", summary="编辑角色信息", name="rbac:roles")
async def edit_roles(role: Role = Body(...)) -> Resp[Role]:
    exists = await engine.exists(Role, Role.id == role.id)
    if not exists:
        raise errors.DataNotFoundError(f"Role(id={role.id})")
    if role.name == "admin":
        raise APIError(code=APIState.PERMISSION_DENIED, msg="Not enough permissions.")
    role = await engine.save(role)
    return Resp(data=role)


@router.delete(
    "/roles/{id}",
    summary="删除角色",
    name="rbac:roles",
)
async def delete_role(id: RoleID = Path(...)) -> Resp[None]:
    await remove_role(id)
    return Resp(data=None)


class PermissionQuery(PaginationQuery):
    name: Optional[PermissionName] = None
    creator: Optional[ObjectId] = Field(default=None, description="创建人")


@router.get(
    "/permissions",
    summary="权限列表",
    name="rbac:permissions",
)
async def get_permissions(query: PermissionQuery = Depends()) -> PageResp[Permission]:
    return await engine.find_pagination(Permission, query)


@router.post("/permissions", summary="新增权限", name="rbac:permissions")
async def post_permission(permission: Annotated[Permission, Body(...)]) -> Resp[Permission]:
    if await engine.exists(Permission, Permission.name == permission.name):
        raise errors.DataNotFoundError(f"Permission(name={permission.name})")
    await engine.upsert_one(permission, Permission.id == permission.id)
    return Resp(data=permission)


async def validate_permission(id: ObjectId = Path(...)) -> Permission:
    permission = await engine.must_find_one(Permission, id=id)
    return permission


@router.put("/permissions", summary="修改权限", name="rbac:permissions")
async def put_permission(permission: Annotated[Permission, Body(...)]) -> Resp[Permission]:
    same_name = await engine.exists(Permission, Permission.name == permission.name, Permission.id != permission.id)
    if same_name:
        raise errors.DataExistedError(f"Permission(name={permission.id})")
    old = await validate_permission(permission.id)
    await engine.save(permission)
    if old.name != permission.name:
        update = {"$push": {"permissions": permission.name}}
        await engine.get_collection(RBACRoute).update_many({}, update)
        await engine.get_collection(Menu).update_many({}, update)
        await engine.get_collection(Role).update_many({}, update)
        update = {"$pull": {"permissions": old.name}}
        await engine.get_collection(RBACRoute).update_many({}, update)
        await engine.get_collection(Menu).update_many({}, update)
        await engine.get_collection(Role).update_many({}, update)
    return Resp(data=permission)


@router.delete("/permissions/{id}", summary="删除权限", name="rbac:permissions")
async def delete_permission(permission: Annotated[Permission, Depends(validate_permission)]) -> Resp[None]:
    await engine.delete(permission)

    update = {"$pull": {"permissions": permission.name}}
    await engine.get_collection(RBACRoute).update_many({}, update)
    await engine.get_collection(Menu).update_many({}, update)
    await engine.get_collection(Role).update_many({}, update)
    return Resp(data=None)


@router.get(
    "/routes",
    summary="路由列表",
    name="rbac:routes",
)
async def get_routes(query: PaginationQuery = Depends()) -> PageResp[RBACRoute]:
    return await engine.find_pagination(RBACRoute, query, {+RBACRoute.deprecated: False})


async def validate_route(id: ObjectId = Path(...)) -> RBACRoute:
    return await engine.must_find_one(RBACRoute, id=id)


class PermissionPost(BaseModel):
    permissions: PermissionNames = Field(...)


@router.post(
    "/routes/{id}/permissions",
    summary="编辑路由权限",
    name="rbac:routes:permissions",
)
async def post_route_permissions(
    update: Annotated[PermissionPost, Body(...)],
    user: RequestUser,
    route: RBACRoute = Depends(validate_route),
) -> Resp[RBACRoute]:
    route.permissions.update(update.permissions)
    await engine.save(route)
    for name in update.permissions:
        if not await engine.exists(Permission, Permission.name == name):
            await engine.save(Permission(name=name, creator=user.id))  # type: ignore
    return Resp(data=route)


class MenuQuery(PaginationQuery):
    sort_by: str = "path"


@router.get("/menus", summary="菜单列表", name="rbac:menus")
async def get_menus(query: Annotated[MenuQuery, Depends()]) -> PageResp[Menu]:
    return await engine.find_pagination(Menu, query)


@router.put("/menus", summary="修改菜单", name="rbac:menus")
@router.post("/menus", summary="新增菜单", name="rbac:menus")
async def post_menu(menu: Annotated[Menu, Body(...)]) -> Resp[Menu]:
    await engine.upsert_one(menu, Menu.id == menu.id)
    return Resp(data=menu)


async def validate_menu(id: ObjectId = Path(...)) -> Menu:
    return await engine.must_find_one(Menu, id=id)


@router.delete("/menus/{id}", summary="删除菜单", name="rbac:menus:remove")
async def delete_menu(menu: Annotated[Menu, Depends(validate_menu)]) -> Resp[None]:
    await engine.delete(menu)
    return Resp(data=None)

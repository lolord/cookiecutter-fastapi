from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, EmailStr
from pydantic.fields import Field

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import SimpleUser, User
from {{cookiecutter.project_name}}.rbac.model import RoleName
from {{cookiecutter.project_name}}.schemas import PageResp, PaginationQuery, Resp
from {{cookiecutter.project_name}}.schemas.errors import DataExistedError, OperateInvalidError
from {{cookiecutter.project_name}}.services.security import (
    auth_admin,
    get_password_hash,
    is_admin,
)
from {{cookiecutter.project_name}}.services.user_service import Nickname, PathUser, user_exists
from {{cookiecutter.project_name}}.settings import settings
from {{cookiecutter.project_name}}.utils import random_password

router = APIRouter(
    prefix="/admin",
    tags=["ADMIN"],
    dependencies=[Depends(auth_admin)],
)


class CreateUser(BaseModel):
    email: EmailStr = Field(..., description="邮箱")
    nickname: Nickname


@router.post(
    "/users",
    summary="管理员创建用户",
    name="admin:users",
)
async def creat_user(body: CreateUser = Body()) -> Resp[SimpleUser]:
    # 密码加密使用原生加密方式
    if await user_exists(email=body.email):
        raise DataExistedError(f"User(email={body.email})")

    password = get_password_hash(random_password(8))
    user = User(nickname=body.nickname, email=body.email, hashed_password=password)  # type: ignore
    await engine.save(user)
    return Resp(data=SimpleUser.validate(user.model_dump()))


class UserInfo(BaseModel):
    password: Optional[str] = Field(None, pattern=settings.PASSWORD_REGEX, description="密码")
    enabled: Optional[bool] = None
    nickname: Optional[Nickname]


@router.put(
    "/users/{id}",
    summary="管理员编辑用户信息",
    name="admin:users",
)
async def admin_edit_user(
    user: PathUser,
    body: UserInfo = Body(...),
) -> Resp[SimpleUser]:
    if body.nickname is not None:
        user.nickname = body.nickname
    if body.password is not None:
        user.hashed_password = get_password_hash(body.password)
    if body.enabled is not None:
        user.enabled = body.enabled

    await engine.save(user)
    return Resp(data=SimpleUser(**user.model_dump()))


@router.post(
    "/reset-password/{id}",
    summary="重置用户密码",
    name="admin:reset-password",
)
async def reset_password(
    user: PathUser,
) -> Resp[str]:
    password = random_password(8)
    user.hashed_password = get_password_hash(password)
    await engine.save(user)
    return Resp(data=password)


@router.delete(
    "/users/{id}",
    summary="管理员删除用户",
    name="admin:users",
)
async def admin_delete_user(
    user: PathUser,
) -> Resp[None]:
    if await is_admin(user):  # pragma: no cover
        raise OperateInvalidError("Cannot delete admin user")
    user.deleted = int(datetime.now().timestamp())
    await engine.save(user)
    return Resp(data=None)


class UsersQuery(PaginationQuery):
    q: Optional[str] = Field(None, description="用户名/邮箱")
    enabled: Optional[bool] = Field(None, description="是否启用")
    roles: Optional[RoleName] = Field(None, description="是否启用")

    keys: List[str] = Field(["email", "nickname"], description="邮箱/名称")


@router.get(
    "/users",
    summary="管理员获取用户列表",
    name="admin:users",
)
async def get_users(query: UsersQuery = Depends()) -> PageResp[SimpleUser]:
    extra_query: Dict[str, Any] = {"deleted": 0}
    return await engine.find_pagination(SimpleUser, query, extra_query)

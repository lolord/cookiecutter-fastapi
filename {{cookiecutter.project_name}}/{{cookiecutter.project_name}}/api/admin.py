from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Path
from pydantic import BaseModel, EmailStr
from pydantic.fields import Field

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import SimpleUser, User, UserID
from {{cookiecutter.project_name}}.rbac.model import RoleName
from {{cookiecutter.project_name}}.schemas import APIState, PageResp, PaginationQuery, Resp
from {{cookiecutter.project_name}}.services.security import (
    auth_admin,
    get_password_hash,
    is_admin,
)
from {{cookiecutter.project_name}}.settings import settings
from {{cookiecutter.project_name}}.utils import random_password

router = APIRouter(
    prefix="/admin",
    tags=["ADMIN"],
)


class CreateUser(BaseModel):
    email: EmailStr = Field(..., description="邮箱")
    nickname: str = Field(
        ...,
        max_length=10,
        min_length=2,
        pattern=settings.USERNAME_REGEX,
        description="姓名",
    )


@router.post(
    "/users",
    summary="管理员创建用户",
    name="admin:users",
)
async def creat_user(
    body: CreateUser = Body(), _=Depends(auth_admin)
) -> Resp[SimpleUser]:
    # 密码加密使用原生加密方式
    password = get_password_hash("123456")
    user = User(nickname=body.nickname, email=body.email, hashed_password=password)  # type: ignore
    await engine.save(user)
    user = await engine.find_one(SimpleUser, SimpleUser.email == body.email)
    return Resp(data=user)


class UserInfo(BaseModel):
    password: Optional[str] = Field(
        None, pattern=settings.PASSWORD_REGEX, description="密码"
    )
    enabled: Optional[bool] = None
    nickname: str = Field(
        None,
        max_length=10,
        min_length=2,
        pattern=settings.USERNAME_REGEX,
        description="姓名",
    )


@router.put(
    "/users/{id}",
    summary="管理员编辑用户信息",
    name="admin:users",
)
async def admin_edit_user(
    id: UserID = Path(..., description="用户id"),
    body: UserInfo = Body(...),
    _=Depends(auth_admin),
) -> Resp[SimpleUser]:
    user = await engine.find_one(User, User.id == id)
    if user is None:  # pragma: no cover
        return Resp(code=APIState.DATA_EXISTED, msg=f"user does not exist:{id}")

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
    id: UserID = Path(..., description="用户id"),
    _=Depends(auth_admin),
) -> Resp[str]:
    user = await engine.find_one(User, User.id == id)
    if user is None:  # pragma: no cover
        return Resp(code=APIState.DATA_EXISTED, msg=f"user does not exist:{id}")
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
    id: UserID = Path(..., description="用户id"),
    _=Depends(auth_admin),
) -> Resp[None]:
    user = await engine.find_one(User, User.id == id)
    if user is None:  # pragma: no cover
        return Resp(code=APIState.DATA_EXISTED, msg=f"user does not exist:{id}")
    if await is_admin(user):  # pragma: no cover
        return Resp(code=APIState.PERMISSION_DENIED, msg="Not enough permissions")
    user.deleted = int(datetime.now().timestamp())
    await engine.save(user)
    return Resp()


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
async def user_system_list(
    query: UsersQuery = Depends(),
    _=Depends(auth_admin),
) -> PageResp[SimpleUser]:
    extra_query: Dict[str, Any] = {"deleted": 0}
    return await engine.find_pagination(SimpleUser, query, extra_query)

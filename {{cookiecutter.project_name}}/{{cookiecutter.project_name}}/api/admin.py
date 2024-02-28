from datetime import datetime
from typing import Any, Dict, Optional

from db import engine
from fastapi import APIRouter, Body, Depends, HTTPException, Path
from models.user import SimpleUser, User, UserID
from pydantic import BaseModel, EmailStr
from pydantic.fields import Field
from rbac.model import Role
from rbac.service import get_role
from schemas import PaginationQuery, PaginationResp
from schemas.response import Resp
from services.security import get_password_hash, is_admin
from settings import settings
from utils import random_password

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
        pattern=r"[\u4e00-\u9fa5a-zA-Z0-9-_]{2,30}$",
        description="姓名",
    )


@router.post(
    "/users",
    summary="管理员创建用户",
    response_model=Resp[SimpleUser],
    name="admin:users",
)
async def creat_user(body: CreateUser = Body()):
    # 密码加密使用原生加密方式
    password = get_password_hash("123456")
    user = User(nickname=body.nickname, email=body.email, hashed_password=password)  # type: ignore
    await engine.save(user)
    user = await engine.find_one(SimpleUser, SimpleUser.email == body.email)
    return Resp(data=user)


class UserBody(BaseModel):
    password: Optional[str] = Field(
        default=None, pattern=settings.PASSWORD_REGEX, description="密码"
    )
    enabled: Optional[bool] = None
    nickname: str = Field(
        ...,
        max_length=10,
        min_length=2,
        pattern=r"[\u4e00-\u9fa5a-zA-Z0-9-_]{2,30}$",
        description="姓名",
    )


@router.put(
    "/users/{id}",
    summary="管理员编辑用户信息",
    response_model=Resp[SimpleUser],
    name="admin:users",
)
async def admin_edit_user(
    id: UserID = Path(..., description="用户id"),
    body: UserBody = Body(...),
):
    user = await engine.find_one(User, User.id == id)
    if user is None:
        raise ValueError(f"user does not exist:{id}")

    if body.nickname is not None:
        user.nickname = body.nickname
    if body.password is not None:
        user.hashed_password = get_password_hash(body.password)
    if body.enabled is not None:
        user.enabled = body.enabled

    await engine.save(user)
    return Resp(data=user.model_dump())


@router.post(
    "/reset-password/{id}",
    summary="重置用户密码",
    response_model=Resp[str],
    name="admin:reset-password",
)
async def reset_password(id: UserID = Path(..., description="用户id")):
    user = await engine.find_one(User, User.id == id)
    if user is None:
        raise ValueError(f"user does not exist:{id}")
    password = random_password(8)
    user.hashed_password = get_password_hash(password)
    await engine.save(user)
    return Resp(data=password)


@router.delete(
    "/users/{id}",
    summary="管理员删除用户",
    response_model=Resp,
    name="admin:users",
)
async def admin_delete_user(
    id: UserID = Path(..., description="用户id"),
):
    user = await engine.find_one(User, User.id == id)
    if user is None:
        raise ValueError(f"user does not exist:{id}")
    if await is_admin(user):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    user.deleted = int(datetime.now().timestamp())
    await engine.save(user)
    return Resp()


class UsersQuery(PaginationQuery):
    q: Optional[str] = Field(None, description="用户名/邮箱")
    enabled: Optional[bool] = Field(None, description="是否启用")


@router.get(
    "/users",
    summary="管理员获取用户列表",
    response_model=PaginationResp[SimpleUser],
    name="admin:users",
)
async def user_system_list(
    query: UsersQuery = Depends(),
    role: Optional[Role] = Depends(get_role),
):
    extra_query: Dict[str, Any] = {"deleted": 0}
    if role:
        extra_query["role"] = role.id
    return await engine.find_pagination(SimpleUser, query, extra_query=extra_query)

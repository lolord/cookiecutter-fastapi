from typing import Optional

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import SimpleUser
from {{cookiecutter.project_name}}.schemas.response import Resp
from {{cookiecutter.project_name}}.services.security import RequestUser, TokenDep, get_password_hash
from {{cookiecutter.project_name}}.services.user_service import Nickname
from {{cookiecutter.project_name}}.settings import settings

router = APIRouter(prefix="/user", tags=["USER"])


class NewPassword(BaseModel):
    password: str = Field(..., pattern=settings.PASSWORD_REGEX, description="新密码")


@router.post("/change-password", summary="修改密码", name="user:change-password")
async def user_change_password(
    token: TokenDep,
    user: RequestUser,
    body: NewPassword = Body(...),
) -> Resp[None]:
    user.hashed_password = get_password_hash(body.password)
    await engine.save(user)
    return Resp(msg="Password updated successfully", data=None)


@router.get("/me", summary="个人信息", name="user:me")
async def get_me(token: TokenDep, user: RequestUser) -> Resp[SimpleUser]:
    return Resp(data=SimpleUser(**user.model_dump()))


class UpdateUser(BaseModel):
    nickname: Optional[Nickname]


@router.put("/me", summary="编辑个人信息", name="user:me")
async def edit_user(
    user: RequestUser,
    doby: UpdateUser = Body(...),
) -> Resp[SimpleUser]:
    if doby.nickname is not None:
        user.nickname = doby.nickname

    await engine.save(user)
    return Resp(data=SimpleUser(**user.model_dump()))

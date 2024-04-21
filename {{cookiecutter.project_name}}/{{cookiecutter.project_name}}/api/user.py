from typing import Optional

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import SimpleUser, User
from {{cookiecutter.project_name}}.schemas.response import Resp
from {{cookiecutter.project_name}}.services.security import auth_current_user, get_password_hash
from {{cookiecutter.project_name}}.settings import settings

router = APIRouter(prefix="/users")


class NewPassword(BaseModel):
    password: str = Field(..., pattern=settings.PASSWORD_REGEX, description="新密码")


@router.post("/change-password", summary="修改密码", name="user:change-password")
async def user_change_password(
    user: User = Depends(auth_current_user),
    body: NewPassword = Body(...),
) -> Resp[None]:
    user.hashed_password = get_password_hash(body.password)
    await engine.save(user)
    return Resp(msg="Password updated successfully")


@router.get("/me", summary="个人信息", name="user:me")
async def me(user: User = Depends(auth_current_user)) -> Resp[SimpleUser]:
    return Resp(data=SimpleUser(**user.model_dump()))


class UpdateUser(BaseModel):
    nickname: Optional[str] = Field(None, min_length=3, max_length=14)


@router.put("/me", summary="编辑个人信息", name="user:me")
async def edit_user(
    doby: UpdateUser = Body(...),
    user: User = Depends(auth_current_user),
) -> Resp[SimpleUser]:
    if doby.nickname is not None:
        user.nickname = doby.nickname

    await engine.save(user)
    return Resp(data=SimpleUser(**user.model_dump()))

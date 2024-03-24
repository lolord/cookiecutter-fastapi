from fastapi import APIRouter, Body, Depends, Path

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import SimpleUser, User, UserID
from {{cookiecutter.project_name}}.schemas.response import APIState, Resp
from {{cookiecutter.project_name}}.services.security import auth_current_user, get_password_hash
from {{cookiecutter.project_name}}.settings import settings

router = APIRouter(prefix="/users")


@router.put("/change-password", summary="修改密码")
async def user_change_password(
    user: User = Depends(auth_current_user),
    password: str = Body(..., pattern=settings.PASSWORD_REGEX, description="新密码"),
) -> Resp[None]:
    user.hashed_password = get_password_hash(password)
    await engine.save(user)
    return Resp(msg="Password updated successfully")


@router.get("/me", summary="简略的个人信息")
async def me(user: User = Depends(auth_current_user)) -> Resp[SimpleUser]:
    return Resp(data=SimpleUser(**user.model_dump()))


@router.put("/me", summary="编辑个人信息")
async def edit_user(
    nickname: str = Body(None, min_length=3, max_length=14),
    user: User = Depends(auth_current_user),
) -> Resp[SimpleUser]:
    if nickname is not None:
        user.nickname = nickname

    await engine.save(user)
    return Resp(data=SimpleUser(**user.model_dump()))


@router.get("/profile/{id}", summary="完整的用户信息")
async def get_profile(
    id: UserID = Path(..., description="user id"),
) -> Resp[SimpleUser]:
    user = await engine.find_one(SimpleUser, SimpleUser.id == id)
    if not user:
        return Resp(code=APIState.DATA_NOT_FOUND, msg="user does not exist")
    return Resp(data=SimpleUser(**user.model_dump()))

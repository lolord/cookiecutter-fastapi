from db import engine
from fastapi import APIRouter, Depends, Form, Path
from models.user import SimpleUser, User, UserID
from schemas.response import Resp
from services.security import auth_current_user, get_password_hash
from settings import settings

router = APIRouter(prefix="/users")


@router.put("/change-password", summary="修改密码")
async def user_change_password(
    user: User = Depends(auth_current_user),
    password: str = Form(..., pattern=settings.PASSWORD_REGEX, description="新密码"),
):
    user.hashed_password = get_password_hash(password)
    await engine.save(user)
    return {"msg": "Password updated successfully"}


@router.get("/me", summary="简略的个人信息", response_model=SimpleUser)
async def me(user: User = Depends(auth_current_user)):
    return user


@router.put("/me", summary="编辑个人信息", response_model=SimpleUser)
async def edit_user(
    nickname: str = Form(None, min_length=3, max_length=14),
    user: User = Depends(auth_current_user),
):
    if nickname is not None:
        user.nickname = nickname

    await engine.save(user)
    return user


@router.get("/postcard/{id}", summary="用户卡片信息", response_model=SimpleUser)
async def get_postcard(id: UserID = Path(..., description="user id")):
    user = await engine.find_one(SimpleUser, SimpleUser.id == id)
    if not user:
        return Resp(code=500, msg="user does not exist")
    return user


@router.get("/profile/{id}", summary="完整的用户信息", response_model=SimpleUser)
async def get_profile(id: UserID = Path(..., description="user id")):
    user = await engine.find_one(SimpleUser, SimpleUser.id == id)
    if not user:
        return Resp(code=500, msg="user does not exist")
    return user

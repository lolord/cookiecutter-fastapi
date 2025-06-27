from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import SimpleUser, User
from {{cookiecutter.project_name}}.schemas import APIState, Resp, Token
from {{cookiecutter.project_name}}.schemas.errors import APIError
from {{cookiecutter.project_name}}.services.security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from {{cookiecutter.project_name}}.services.user_service import user_exists
from {{cookiecutter.project_name}}.settings import settings

router = APIRouter(prefix="/auth", tags=["AUTH"])


@router.get(
    "/user-exists",
    summary="检测用户是否存在",
    name="auth:user-exists",
)
async def get_user_exists(
    email: EmailStr = Query(..., description="账户"),
) -> Resp[bool]:
    exists: bool = await engine.exists(User, User.email == email) > 0
    return Resp(data=exists)


class Register(BaseModel):
    password: str = Field(..., pattern=settings.PASSWORD_REGEX, description="密码")
    email: EmailStr = Field(..., description="邮箱")
    nickname: str = Field(
        ...,
        max_length=10,
        min_length=2,
        pattern=settings.USERNAME_REGEX,
        description="姓名",
    )


@router.post("/register", summary="注册", name="auth:register")
async def auth_regsiter(
    resister: Register = Body(),
) -> Resp[SimpleUser]:
    if not settings.USERS_OPEN_REGISTRATION:
        raise APIError(
            code=APIState.PERMISSION_DENIED,
            msg="User registration not open",
        )
    if await user_exists(email=resister.email):
        raise APIError(
            code=APIState.DATA_EXISTED,
            msg="The email has been registered",
        )

    hashed_password = get_password_hash(resister.password)
    user = User(
        nickname=resister.nickname,
        email=resister.email,
        hashed_password=hashed_password,
    )  # type: ignore
    await engine.save(user)
    return Resp(data=SimpleUser(**user.model_dump()))


class Login(BaseModel):
    password: str = Field(
        ...,
        max_length=24,
        min_length=6,
        pattern=settings.PASSWORD_REGEX,
        description="密码",
    )

    email: EmailStr = Field(..., description="邮箱")


@router.post("/login", summary="登录", name="auth:login")
async def auth_login(login: Login = Body()) -> Resp[Token]:
    user = await authenticate_user(login.email, login.password)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return Resp(data=Token(access_token=access_token, token_type="bearer"))


@router.post("/oauth2login", summary="OAuth2登录", name="auth:oauth2login")
async def oauth2login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    resp = await auth_login(
        login=Login(
            email=form_data.username,
            password=form_data.password,
        )
    )
    return resp.data


@router.post("/logout", summary="登出", name="auth:logout")
async def logout() -> Resp[bool]:
    return Resp(data=True)

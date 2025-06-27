from typing import Annotated, Optional, TypeAlias

from fastapi import Depends, Path
from odmantic import ObjectId
from pydantic import EmailStr, Field

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import User, UserID
from {{cookiecutter.project_name}}.schemas.errors import DataNotFoundError
from {{cookiecutter.project_name}}.settings import settings


async def get_user_by_id(id: ObjectId | str) -> Optional[User]:
    return await engine.find_one(User, User.id == id)


async def get_user_by_email(email: EmailStr) -> Optional[User]:
    return await engine.find_one(User, User.email == email)


async def user_exists(email: EmailStr) -> bool:
    user = await get_user_by_email(email=email)
    return True if user else False


async def path_user(id: UserID = Path(..., description="用户id")) -> User:
    user = await get_user_by_id(id)
    if user is None:
        raise DataNotFoundError(f"User(id={id})")
    return user


PathUser: TypeAlias = Annotated[User, Depends(path_user)]
Nickname: TypeAlias = Annotated[
    str,
    Field(
        ...,
        max_length=32,
        min_length=2,
        pattern=settings.USERNAME_REGEX,
        description="姓名",
    ),
]

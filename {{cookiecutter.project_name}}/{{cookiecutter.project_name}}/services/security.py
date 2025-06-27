from datetime import datetime, timedelta
from typing import Annotated, Optional, TypeAlias, cast

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import EmailStr

from {{cookiecutter.project_name}}.models.user import User
from {{cookiecutter.project_name}}.schemas.errors import LoginFailedError, PermissionDeniedError
from {{cookiecutter.project_name}}.services.user_service import get_user_by_email
from {{cookiecutter.project_name}}.settings import settings

SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_VER}/auth/oauth2login")
TokenDep = Annotated[str, Depends(oauth2_scheme)]

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

forbidden_exception = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Permission denied",
    headers={"WWW-Authenticate": "Bearer"},
)


not_enough_permissions = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not enough permissions",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    result: bool = pwd_context.verify(plain_password, hashed_password)
    return result


def get_password_hash(password: str) -> str:
    return cast(str, pwd_context.hash(password))


async def jwt_required(token: TokenDep) -> EmailStr:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: EmailStr = cast(EmailStr, payload.get("sub"))
        return email
    except InvalidTokenError:
        raise credentials_exception


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    email: Annotated[EmailStr, Depends(jwt_required)],
) -> Optional[User]:  # pragma: no cover
    return await get_user_by_email(email)


async def get_request_user(request: Request) -> Optional[User]:
    return cast(Optional[User], getattr(request.state, "user", None))


def auth_user(user: User | None = Depends(get_request_user)) -> User:
    if not user:
        raise LoginFailedError(msg="Incorrect email or password")
    if user.deleted:
        raise LoginFailedError(msg="User deleted")
    if not user.enabled:
        raise LoginFailedError(msg="Inactive user")
    if user.expire_at is not None and user.expire_at < datetime.now():
        raise LoginFailedError(msg="User has expired")

    return user


async def authenticate_user(email: EmailStr, password: str) -> User:
    _user = await get_user_by_email(email)
    user = auth_user(_user)
    if not verify_password(password, user.hashed_password):
        raise LoginFailedError(msg="Incorrect password")
    return user


RequestUser: TypeAlias = Annotated[User, Depends(auth_user)]


async def is_admin(user: RequestUser) -> bool:
    return "admin" in user.roles


async def auth_admin(user: RequestUser) -> User:
    admin = await is_admin(user)
    if admin:
        return user
    else:
        raise PermissionDeniedError("admin")

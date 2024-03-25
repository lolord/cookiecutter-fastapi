from datetime import datetime, timedelta
from typing import Optional, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from jose import JWTError, jwt
from odmantic.query import in_
from passlib.context import CryptContext
from pydantic import EmailStr

from {{cookiecutter.project_name}}.db import engine
from {{cookiecutter.project_name}}.models.user import User
from {{cookiecutter.project_name}}.rbac.model import PermissionNames, RBACRoute, Role
from {{cookiecutter.project_name}}.schemas import PermissionDeniedError, RBACRouteNotFindError
from {{cookiecutter.project_name}}.settings import settings

SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ALGORITHM = "HS256"

oauth2_scheme = APIKeyHeader(name="Access-Token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user_by_nickname(nickname: EmailStr) -> Optional[User]:
    user = await engine.find_one(User, User.nickname == nickname)
    return user


async def jwt_required(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = cast(str, payload.get("sub"))
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = cast(str, payload.get("sub"))
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return await get_user_by_email(email)


async def authenticate_user(email: EmailStr, password: str) -> User:
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if user.deleted:
        raise HTTPException(status_code=400, detail="User deleted")
    if not user.enabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if user.expire_at is not None and user.expire_at < datetime.now():
        raise HTTPException(status_code=400, detail="User has expired")
    return user


async def get_user_by_email(email: str) -> Optional[User]:
    return await engine.find_one(User, User.email == email)


async def user_exists(email: str) -> bool:
    user = await get_user_by_email(email=email)
    return True if user else False


async def get_user_permissions(
    user: User = Depends(get_current_user),
) -> PermissionNames:
    permissions = set()
    if user.roles:
        async for role in engine.find(Role, in_(Role.name, user.roles)):
            permissions.update(role.permissions)
    return permissions


async def get_api_permissions(request: Request) -> PermissionNames:
    """适用于endpoint function dependencies"""
    method = request.method
    path = request.url.path

    router = request.scope.get("router")
    endpoint = request.scope.get("endpoint")
    if router and endpoint:
        for route in router.routes:
            route_app = getattr(route, "app", None)
            route_endpoint = getattr(route, "endpoint", None)
            if endpoint in (route_app, route_endpoint):
                path = route.path
                break

    rbac_route = await engine.find_one(
        RBACRoute, RBACRoute.method == method, RBACRoute.path == path
    )

    if not rbac_route:
        raise RBACRouteNotFindError(method, path)

    permissions = set()
    if rbac_route.permissions:
        async for role in engine.find(
            Role,
            in_(Role.permissions, rbac_route.permissions),  # no
        ):
            permissions.update(role.permissions)
    return permissions


async def auth_api_permission(
    user_permissions: PermissionNames = Depends(get_user_permissions),
    api_permissions: PermissionNames = Depends(get_api_permissions),
) -> PermissionNames:
    permissions = user_permissions & api_permissions
    if not permissions:
        raise PermissionDeniedError(api_permissions)
    return permissions


async def auth_current_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if user is None:
        raise credentials_exception

    if user.enabled is False:
        raise credentials_exception

    # user.__dict__["permissions"] = await auth_api_permission(user)

    return user


async def is_admin(user: User = Depends(get_current_user)) -> bool:
    return "admin" in user.roles


async def auth_admin(user: User = Depends(auth_current_user)) -> User:
    admin = await is_admin(user)
    if admin:
        return user
    else:
        raise HTTPException(status_code=400, detail="Not enough permissions")

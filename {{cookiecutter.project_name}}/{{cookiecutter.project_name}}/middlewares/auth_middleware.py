from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from {{cookiecutter.project_name}}.services.security import jwt_required, oauth2_scheme
from {{cookiecutter.project_name}}.services.user_service import get_user_by_email


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        token: str | None = None
        try:
            token = await oauth2_scheme(request)
            if token is not None:
                email = await jwt_required(token)
                user = await get_user_by_email(email)
                if user is not None:
                    setattr(request.state, "user", user)
        except StarletteHTTPException:
            # 访客访问
            pass
        return await call_next(request)

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from {{cookiecutter.project_name}}.api import admin, auth, dashboard, publics, user
from {{cookiecutter.project_name}}.middlewares.auth_middleware import AuthMiddleware
from {{cookiecutter.project_name}}.rbac import api as rbac
from {{cookiecutter.project_name}}.rbac.middleware import RBACMiddleware
from {{cookiecutter.project_name}}.schemas.errors import APIError
from {{cookiecutter.project_name}}.services.security import jwt_required
from {{cookiecutter.project_name}}.settings import settings
from {{cookiecutter.project_name}}.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(f"startup: {settings.ENV_STATE}")
    await RBACMiddleware.update_rbac_routes(app)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    debug=settings.DEBUG,
    default_response_class=ORJSONResponse,
)

statics = os.path.join(os.path.basename(__name__), settings.PROJECT_NAME, "statics")
app.mount("/statics", StaticFiles(directory=statics), name="statics")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> Response:
    resp = await http_exception_handler(request, exc)
    return resp


@app.exception_handler(APIError)
async def handler_api_error(request: Request, error: APIError) -> Response:
    logger.exception(error)
    return ORJSONResponse(
        content=jsonable_encoder(error.response()),
        status_code=status.HTTP_400_BAD_REQUEST,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RBACMiddleware)
app.add_middleware(AuthMiddleware)


@app.get("/docsx", include_in_schema=False)
async def custom_swagger_ui_html() -> Response:
    assert app.openapi_url
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.21.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.21.0/swagger-ui.css",
        swagger_favicon_url="/statics/api-docs/favicon.png",
    )


app.include_router(publics.router)
app.include_router(auth.router, prefix=settings.API_VER)
app.include_router(user.router, prefix=settings.API_VER)
app.include_router(admin.router, prefix=settings.API_VER, dependencies=[Depends(jwt_required)])
app.include_router(dashboard.router, prefix=settings.API_VER)
app.include_router(rbac.router, prefix=settings.API_VER)


# uvicorn {{cookiecutter.project_name}}.main:app --host 127.0.0.1 --port 5000 --reload
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        access_log=True,
    )

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import ORJSONResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from odmantic.exceptions import DocumentParsingError
from starlette import status
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from {{cookiecutter.project_name}}.api import admin, auth, dashboard, publics, user
from {{cookiecutter.project_name}}.rbac.api import router as rbac_router
from {{cookiecutter.project_name}}.rbac.middleware import RBACMiddleware
from {{cookiecutter.project_name}}.schemas.errors import APIException
from {{cookiecutter.project_name}}.services.security import (
    get_current_user,
    get_user_permissions,
    jwt_required,
)
from {{cookiecutter.project_name}}.settings import settings
from {{cookiecutter.project_name}}.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
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

if not os.path.exists(settings.STATICS_DIR):
    os.mkdir(settings.STATICS_DIR)


app.mount("/statics", StaticFiles(directory="statics"), name="statics")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.exception_handler(ValueError)
async def handler_value_error(request: Request, error: ValueError):
    if isinstance(error, DocumentParsingError):
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                {"detail": error.inner.errors(), "body": error.inner.title}
            ),
        )
    else:
        return ORJSONResponse(
            jsonable_encoder({"error": str(error)}),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)


@app.exception_handler(APIException)
async def handler_api_error(request: Request, error: APIException):
    return ORJSONResponse(
        jsonable_encoder(str(error)),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.exception_handler(Exception)
async def handler_unknown_error(request: Request, error: Exception):
    return ORJSONResponse(
        jsonable_encoder(str(error)),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RBACMiddleware)


app.include_router(auth.router, prefix=settings.API_VER, tags=["AUTH"])
app.include_router(user.router, prefix=settings.API_VER, tags=["USER"])
app.include_router(
    admin.router,
    prefix=settings.API_VER,
    tags=["ADMIN"],
    dependencies=[Depends(jwt_required)],
)

app.include_router(
    rbac_router, prefix=settings.API_VER, dependencies=[Depends(jwt_required)]
)
app.include_router(dashboard.router, prefix=settings.API_VER, tags=["DASHBOARD"])
app.include_router(publics.router, tags=["PUBLICS"])


@app.middleware("http")
async def set_user(request: Request, call_next):
    user = None
    try:
        token = await APIKeyHeader(name="Access-Token")(request)
        if token is not None:
            user = await get_current_user(token)
    except HTTPException:
        ...

    if user is not None:
        user.permissions = await get_user_permissions(user)
        setattr(request.state, "user", user)

    return await call_next(request)


@app.get("/docsx", include_in_schema=False)
async def custom_swagger_ui_html():
    assert app.openapi_url
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        # from cdn
        # swagger_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.5.0/swagger-ui-bundle.js",
        # swagger_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.5.0/swagger-ui.css",
        # from local
        swagger_js_url="/statics/api-docs/swagger/swagger-ui-bundle.js",
        swagger_css_url="/statics/api-docs/swagger/swagger-ui.css",
        swagger_favicon_url="/statics/api-docs/favicon.png",
    )


# uvicorn main:app --host 127.0.0.1 --port 5000 --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        access_log=True,
    )

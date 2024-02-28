import os
from contextlib import asynccontextmanager

from api import admin, auth, dashboard, user
from extends.logger import logger
from fastapi import Depends, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from rbac.api import router as rbac_router
from rbac.service import update_rbac_routes
from schemas.errors import APIException
from services.security import (get_current_user, get_user_permissions,
                               jwt_required)
from settings import settings
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    debug=settings.DEBUG,
)


if not os.path.exists(settings.STATICS_DIR):
    os.mkdir(settings.STATICS_DIR)

app.mount("/statics", StaticFiles(directory="statics"), name="statics")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"startup: {settings.ENV_STATE}")
    await update_rbac_routes(app)
    yield


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.exception_handler(ValueError)
async def handler_value_error(request: Request, error: ValueError):
    return JSONResponse(jsonable_encoder({"msg": str(error)}), status_code=500)


@app.exception_handler(APIException)
async def handler_timeout_error(request: Request, error: APIException):
    return JSONResponse(jsonable_encoder(str(error)), status_code=500)


@app.exception_handler(HTTPException)
async def http_error(request: Request, error: APIException):
    return JSONResponse(jsonable_encoder(repr(error)), status_code=500)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(RBACMiddleware)


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
        user.permissions = list(await get_user_permissions(user))

    request.scope["user"] = user

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
        swagger_js_url="/statics/api-docs/swagger/swagger-ui-bundle.min.js",
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

from fastapi import APIRouter

from {{cookiecutter.project_name}}.settings import settings

router = APIRouter(prefix="/publics")


@router.get("/hello", summary="测试接口", name="publics:hello")
async def hello():
    return "hello"


@router.get("/app", summary="App description", name="publics:app")
async def get_app():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
    }

from fastapi import APIRouter

from {{cookiecutter.project_name}}.settings import settings

router = APIRouter(prefix="/publics", tags=["PUBLICS"])


@router.get("/hello", summary="测试接口", name="publics:hello")
async def hello() -> str:
    return "hello"


def app_description() -> dict[str, str]:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
    }


@router.get("/app", summary="App description", name="publics:app")
async def get_app() -> dict[str, str]:
    return app_description()

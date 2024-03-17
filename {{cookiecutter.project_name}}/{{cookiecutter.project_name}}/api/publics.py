from fastapi import APIRouter
from pydantic import BaseModel
from settings import settings

router = APIRouter(prefix="/publics")


class Message(BaseModel):
    message: str


responses = {
    404: {"model": Message, "description": "Item not found"},
    302: {"description": "The item was moved"},
    403: {"description": "Not enough privileges"},
}


@router.post(
    "/responses-schemas",
    summary="Responses Schemas",
    response_model=None,
    responses=responses,  # type: ignore
)
async def reset_system():
    return None


@router.get("/hello", summary="测试接口")
async def hello():
    return "hello"


@router.get("/app", summary="App information")
async def get_app():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
    }

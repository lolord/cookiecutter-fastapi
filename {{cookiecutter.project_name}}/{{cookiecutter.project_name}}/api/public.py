from fastapi import APIRouter

router = APIRouter(prefix="/common")


@router.post("/reset-system", summary="重置系统", response_model=None)
async def reset_system():
    return None


@router.get("/hello", summary="测试接口", response_model=None)
async def hello():
    return "hello"

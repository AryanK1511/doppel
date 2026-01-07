from fastapi import APIRouter
from src.common.utils.response import Response

router = APIRouter(prefix="/reel", tags=["reel"])


@router.post("/generate", response_model=None)
async def generate_reel():
    return Response.success(
        message="Reel generated successfully", data={"image": "image.png"}
    )

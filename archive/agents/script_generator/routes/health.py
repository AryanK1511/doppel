import socket

from common.logger import logger
from common.utils.response import Response
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/")
@router.get("/health")
@router.get("/healthz")
async def health_check(request: Request):
    logger.info("Server is Healthy")
    app = request.app
    return Response.success(
        message="Server is Healthy",
        data={
            "status": "ok",
            "hostname": socket.gethostname(),
            "version": getattr(app, "version", "0.1.0"),
        },
    )

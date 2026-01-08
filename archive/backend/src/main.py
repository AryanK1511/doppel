import socket
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.common.constants import PROJECT_TITLE
from src.common.logger import logger, setup_logging
from src.common.utils.exception_handlers import register_exception_handlers
from src.database.mongodb.mongodb_client import mongodb_client
from src.module.audio.audio_controller import router as audio_router
from src.module.reel.controller.reel_controller import router as reel_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb_client.connect()
    yield
    await mongodb_client.disconnect()


def create_app() -> FastAPI:
    setup_logging()

    try:
        app_version = version("viralens-backend-service")
    except Exception:
        app_version = "0.1.0"

    app: FastAPI = FastAPI(
        title=PROJECT_TITLE,
        servers=[
            {
                "url": "http://127.0.0.1:8000",
                "description": "Local Development Server",
            },
        ],
        summary="Viralens Backend Service API",
        description="Viralens Backend Service API",
        version=app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(audio_router)
    app.include_router(reel_router)
    return app


# ========== FAST API APPLICATION ==========
app: FastAPI = create_app()


# ========== HEALTH CHECK ROUTES ==========
@app.get("/")
@app.get("/health")
@app.get("/healthz")
async def health_check() -> JSONResponse:
    logger.info("Server is Healthy")
    return JSONResponse(
        content={
            "status": "ok",
            "hostname": socket.gethostname(),
            "version": app.version,
        }
    )

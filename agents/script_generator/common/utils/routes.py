from fastapi import FastAPI

from routes.health import router as health_router


def include_routers(app: FastAPI) -> None:
    app.include_router(health_router)

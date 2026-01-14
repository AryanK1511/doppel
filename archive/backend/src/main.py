import asyncio
import socket
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.common.constants import PROJECT_TITLE
from src.common.logger import logger, setup_logging
from src.common.utils.exception_handlers import register_exception_handlers
from src.common.utils.response import Response
from src.database.mongodb.mongodb_client import mongodb_client
from src.module.agent.agent_controller import router as agent_router
from src.module.conversation.conversation_controller import (
    router as conversation_router,
)
from src.module.conversation.conversation_dependency import get_conversation_service
from src.module.world.world_controller import router as world_router
from src.module.world.world_dependency import get_world_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb_client.connect()
    yield
    await mongodb_client.disconnect()


def create_app() -> FastAPI:
    setup_logging()

    try:
        app_version = version("doppel-backend")
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
        summary="Doppel AI Networking Platform API",
        description="AI agents that network, interview, and match 24/7 so you don't have to.",
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

    app.include_router(agent_router)
    app.include_router(conversation_router)
    app.include_router(world_router)

    register_exception_handlers(app)

    return app


# ========== FAST API APPLICATION ==========
app: FastAPI = create_app()


# ========== HEALTH CHECK ROUTES ==========
@app.get("/")
@app.get("/health")
@app.get("/healthz")
async def health_check() -> JSONResponse:
    logger.info("Server is Healthy")
    return Response.success(
        message="Server is Healthy",
        data={
            "status": "ok",
            "hostname": socket.gethostname(),
            "version": app.version,
        },
    )


# ========== WEBSOCKET ENDPOINTS ==========
@app.websocket("/ws/test")
async def test_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("Test WebSocket connected!")
    await websocket.send_json({"message": "Hello from WebSocket!"})
    await websocket.close()


@app.websocket("/ws/world")
async def world_websocket(websocket: WebSocket):
    try:
        await websocket.accept()
        logger.info("World WebSocket connected")
    except Exception as e:
        logger.error(f"Failed to accept WebSocket: {e}", exc_info=True)
        return

    try:
        world_service = get_world_service()
    except Exception as e:
        logger.error(f"Failed to get world service: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Service initialization failed")
        except Exception:
            pass
        return

    queue: asyncio.Queue = asyncio.Queue()

    async def state_callback(state: dict):
        await queue.put(state)

    try:
        world_service.add_state_callback(state_callback)
    except Exception as e:
        logger.error(f"Failed to add state callback: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Failed to register callback")
        except Exception:
            pass
        return

    try:
        while True:
            try:
                state = await asyncio.wait_for(queue.get(), timeout=1.0)
                await websocket.send_json(state)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        logger.info("World WebSocket disconnected")
    except Exception as e:
        logger.error(f"World WebSocket error: {e}", exc_info=True)
    finally:
        try:
            world_service.remove_state_callback(state_callback)
        except Exception as e:
            logger.error(f"Failed to remove state callback: {e}", exc_info=True)


@app.websocket("/conversation/ws/{conversation_id}")
async def conversation_websocket(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    logger.info(f"Conversation WebSocket connected for {conversation_id}")

    conversation_service = get_conversation_service()

    try:
        async for turn in conversation_service.run_conversation_stream(conversation_id):
            await websocket.send_json(
                {
                    "type": "turn",
                    "data": {
                        "role": turn.role,
                        "speaker_name": turn.speaker_name,
                        "content": turn.content,
                        "timestamp": turn.timestamp,
                        "is_final": turn.is_final,
                        "final_evaluation": turn.final_evaluation,
                    },
                }
            )

        await websocket.send_json({"type": "complete"})
        logger.info(f"Conversation {conversation_id} completed via WebSocket")

    except WebSocketDisconnect:
        logger.info(f"Conversation WebSocket disconnected for {conversation_id}")
    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
    except Exception as e:
        logger.error(f"Conversation WebSocket error for {conversation_id}: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()

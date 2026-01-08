from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from ai.agent import ContentStrategistAgent
from ai.agent_executor import ContentStrategistAgentExecutor
from common.constants import PROJECT_TITLE
from common.logger import setup_logging
from common.utils.exception_handlers import register_exception_handlers
from common.utils.routes import include_routers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse


def create_app() -> FastAPI:
    setup_logging()

    skill = AgentSkill(
        id="content-strategist",
        name="Content Strategist",
        description="A content strategist that helps with content creation for short-form content like TikTok reels, Instagram posts, and YouTube videos.",
        tags=["content", "strategist", "creation"],
        examples=[
            "I need content strategy for a TikTok reel about the latest trends in AI",
            "I need a content strategy for an Instagram reel about the top 5 most popular movies of 2025",
        ],
    )

    agent_card = AgentCard(
        name="content-strategist",
        description="A content strategist that helps with content creation for short-form content like TikTok reels, Instagram posts, and YouTube videos.",
        url="http://localhost:8000/",
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[skill],
        version="0.1.0",
        capabilities=AgentCapabilities(),
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ContentStrategistAgentExecutor(ContentStrategistAgent()),
        task_store=InMemoryTaskStore(),
    )

    server = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    app = server.build()

    app.title = PROJECT_TITLE
    app.version = "0.1.0"
    app.summary = "Content Strategist Agent API"
    app.description = "Content Strategist Agent API"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    include_routers(app)
    register_exception_handlers(app)

    return app


app: FastAPI = create_app()


@app.get("/favicon.ico")
async def favicon_handler() -> StarletteResponse:
    return StarletteResponse(status_code=204)

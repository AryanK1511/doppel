from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from src.common.logger import logger
from src.common.utils.response import Response, Status
from src.module.conversation.conversation_dependency import get_conversation_service
from src.module.conversation.conversation_schema import (
    ConversationListItem,
    ConversationResult,
    MatchResult,
    StartConversationRequest,
)
from src.module.conversation.conversation_service import ConversationService

router = APIRouter(prefix="/conversation", tags=["conversations"])


@router.post("/start")
async def start_conversation(
    request: StartConversationRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    try:
        result = await conversation_service.start_conversation(
            recruiter_id=request.recruiter_id,
            candidate_id=request.candidate_id,
        )
        return Response.success(
            message="Conversation started successfully",
            data=result,
            status_code=Status.CREATED,
        )
    except ValueError as e:
        return Response.error(
            message=str(e),
            status_code=Status.BAD_REQUEST,
        )
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        return Response.error(
            message=f"Failed to start conversation: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.websocket("/ws/{conversation_id}")
async def conversation_websocket(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for conversation {conversation_id}")

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
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except ValueError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
    except Exception as e:
        logger.error(f"WebSocket error for conversation {conversation_id}: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()


@router.get("", response_model=list[ConversationListItem])
async def get_all_conversations(
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    try:
        result = await conversation_service.get_all_conversations()
        return Response.success(
            message="Conversations retrieved successfully",
            data=result,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to retrieve conversations: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/matches", response_model=list[MatchResult])
async def get_matches(
    min_score: int | None = Query(None, ge=1, le=10),
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    try:
        result = await conversation_service.get_matches(min_score=min_score)
        return Response.success(
            message="Matches retrieved successfully",
            data=result,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to retrieve matches: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/{conversation_id}", response_model=ConversationResult)
async def get_conversation(
    conversation_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    try:
        result = await conversation_service.get_conversation(conversation_id)
        return Response.success(
            message="Conversation retrieved successfully",
            data=result,
        )
    except ValueError as e:
        return Response.error(
            message=str(e),
            status_code=Status.NOT_FOUND,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to retrieve conversation: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/agent/{agent_id}", response_model=list[ConversationListItem])
async def get_conversations_for_agent(
    agent_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    try:
        result = await conversation_service.get_conversations_for_agent(agent_id)
        return Response.success(
            message="Conversations retrieved successfully",
            data=result,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to retrieve conversations: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )

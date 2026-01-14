from src.database.mongodb.mongodb_client import mongodb_client
from src.module.conversation.conversation_dependency import get_conversation_service
from src.module.world.world_service import WorldService

_world_service: WorldService | None = None


def get_world_service() -> WorldService:
    global _world_service
    if _world_service is None:
        conversation_service = get_conversation_service()
        _world_service = WorldService(mongodb_client, conversation_service)
    return _world_service

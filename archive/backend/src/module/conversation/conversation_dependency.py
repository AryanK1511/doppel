from src.database.mongodb.mongodb_client import mongodb_client
from src.module.conversation.conversation_service import ConversationService

_conversation_service: ConversationService | None = None


def get_conversation_service() -> ConversationService:
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService(mongodb_client)
    return _conversation_service

from fastapi import Depends
from src.database.db_dependency import get_mongodb_client
from src.database.mongodb.mongodb_client import MongoDBClient
from src.module.agent.agent_service import AgentService


def get_agent_service(
    mongodb_client: MongoDBClient = Depends(get_mongodb_client),
) -> AgentService:
    return AgentService(mongodb_client=mongodb_client)

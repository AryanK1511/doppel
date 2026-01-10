from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from src.common.logger import logger
from src.database.mongodb.mongodb_client import MongoDBClient


class AgentService:
    def __init__(self, mongodb_client: MongoDBClient):
        self.mongodb_client = mongodb_client

    async def create_agent(
        self, username: str, name: str, bio: str, type: str
    ) -> dict[str, Any]:
        if type not in ["candidate", "recruiter"]:
            raise ValueError("Type must be either 'candidate' or 'recruiter'")

        existing_agent = await self.mongodb_client.agents.find_one(
            {"username": username}
        )
        if existing_agent:
            raise ValueError(f"Agent with username '{username}' already exists")

        agent_doc = {
            "username": username,
            "name": name,
            "bio": bio,
            "type": type,
            "created_at": datetime.utcnow(),
        }
        result = await self.mongodb_client.agents.insert_one(agent_doc)
        agent_doc["_id"] = result.inserted_id

        logger.info(
            f"Created agent: {name} with username: {username} and id: {result.inserted_id}"
        )

        return {
            "agent_id": str(agent_doc["_id"]),
            "username": agent_doc["username"],
            "name": agent_doc["name"],
            "bio": agent_doc["bio"],
            "type": agent_doc["type"],
            "created_at": agent_doc["created_at"].isoformat(),
        }

    async def get_all_agents(self) -> list[dict[str, Any]]:
        cursor = self.mongodb_client.agents.find().sort("created_at", -1)
        agents = await cursor.to_list(length=None)

        result = []
        for agent in agents:
            result.append(
                {
                    "agent_id": str(agent["_id"]),
                    "username": agent["username"],
                    "name": agent["name"],
                    "bio": agent["bio"],
                    "type": agent["type"],
                    "created_at": agent["created_at"].isoformat(),
                }
            )

        return result

    async def get_agent_by_id(self, agent_id: str) -> dict[str, Any]:
        try:
            agent = await self.mongodb_client.agents.find_one(
                {"_id": ObjectId(agent_id)}
            )
        except Exception:
            raise ValueError(f"Invalid agent ID format: {agent_id}")

        if not agent:
            raise ValueError(f"Agent with id {agent_id} not found")

        return {
            "agent_id": str(agent["_id"]),
            "username": agent["username"],
            "name": agent["name"],
            "bio": agent["bio"],
            "type": agent["type"],
            "created_at": agent["created_at"].isoformat(),
        }

    async def update_agent(
        self,
        agent_id: str,
        username: Optional[str],
        name: Optional[str],
        bio: Optional[str],
        type: Optional[str],
    ) -> dict[str, Any]:
        if type and type not in ["candidate", "recruiter"]:
            raise ValueError("Type must be either 'candidate' or 'recruiter'")

        try:
            object_id = ObjectId(agent_id)
        except Exception:
            raise ValueError(f"Invalid agent ID format: {agent_id}")

        if username is not None:
            existing_agent = await self.mongodb_client.agents.find_one(
                {"username": username, "_id": {"$ne": object_id}}
            )
            if existing_agent:
                raise ValueError(f"Agent with username '{username}' already exists")

        update_data = {}
        if username is not None:
            update_data["username"] = username
        if name is not None:
            update_data["name"] = name
        if bio is not None:
            update_data["bio"] = bio
        if type is not None:
            update_data["type"] = type

        if not update_data:
            raise ValueError("At least one field must be provided for update")

        result = await self.mongodb_client.agents.update_one(
            {"_id": object_id}, {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ValueError(f"Agent with id {agent_id} not found")

        agent = await self.mongodb_client.agents.find_one({"_id": object_id})

        logger.info(f"Updated agent: {agent_id}")

        return {
            "agent_id": str(agent["_id"]),
            "username": agent["username"],
            "name": agent["name"],
            "bio": agent["bio"],
            "type": agent["type"],
            "created_at": agent["created_at"].isoformat(),
        }

    async def delete_agent(self, agent_id: str) -> None:
        try:
            object_id = ObjectId(agent_id)
        except Exception:
            raise ValueError(f"Invalid agent ID format: {agent_id}")

        result = await self.mongodb_client.agents.delete_one({"_id": object_id})

        if result.deleted_count == 0:
            raise ValueError(f"Agent with id {agent_id} not found")

        logger.info(f"Deleted agent: {agent_id}")

    async def delete_all_agents(self) -> int:
        result = await self.mongodb_client.agents.delete_many({})
        count = result.deleted_count

        logger.info(f"Deleted {count} agents")

        return count

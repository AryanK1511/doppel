from datetime import datetime
from typing import Any, Optional

from bson import ObjectId
from src.common.logger import logger
from src.database.mongodb.mongodb_client import MongoDBClient
from src.module.agent.agent_schema import (
    RecruiterProfile,
    CandidateProfile,
    UpdateRecruiterProfile,
    UpdateCandidateProfile,
)


class AgentService:
    def __init__(self, mongodb_client: MongoDBClient):
        self.mongodb_client = mongodb_client

    def _extract_name_and_bio(self, profile: dict, agent_type: str) -> tuple[str, str]:
        if agent_type == "recruiter":
            return profile.get("name", ""), profile.get("bio", "")
        elif agent_type == "candidate":
            personal_info = profile.get("personal_info", {})
            name = personal_info.get("full_name", "")
            bio = profile.get("professional_summary", "")
            return name, bio
        return "", ""

    async def create_agent(
        self, username: str, agent_type: str, profile: dict
    ) -> dict[str, Any]:
        if agent_type not in ["candidate", "recruiter"]:
            raise ValueError("Type must be either 'candidate' or 'recruiter'")

        existing_agent = await self.mongodb_client.agents.find_one(
            {"username": username}
        )
        if existing_agent:
            raise ValueError(f"Agent with username '{username}' already exists")

        if agent_type == "recruiter":
            try:
                RecruiterProfile(**profile)
            except Exception as e:
                raise ValueError(f"Invalid recruiter profile: {str(e)}")
        elif agent_type == "candidate":
            try:
                CandidateProfile(**profile)
            except Exception as e:
                raise ValueError(f"Invalid candidate profile: {str(e)}")

        name, bio = self._extract_name_and_bio(profile, agent_type)

        agent_doc = {
            "username": username,
            "name": name,
            "bio": bio,
            "type": agent_type,
            "profile": profile,
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
            "profile": agent_doc["profile"],
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

        profile = agent.get("profile", {})

        return {
            "agent_id": str(agent["_id"]),
            "username": agent["username"],
            "name": agent["name"],
            "bio": agent["bio"],
            "type": agent["type"],
            "profile": profile,
            "created_at": agent["created_at"].isoformat(),
        }

    async def update_agent(
        self,
        agent_id: str,
        username: Optional[str],
        agent_type: Optional[str],
        profile: Optional[dict],
    ) -> dict[str, Any]:
        if agent_type and agent_type not in ["candidate", "recruiter"]:
            raise ValueError("Type must be either 'candidate' or 'recruiter'")

        try:
            object_id = ObjectId(agent_id)
        except Exception:
            raise ValueError(f"Invalid agent ID format: {agent_id}")

        existing_agent = await self.mongodb_client.agents.find_one({"_id": object_id})
        if not existing_agent:
            raise ValueError(f"Agent with id {agent_id} not found")

        current_type = existing_agent.get("type")
        final_type = agent_type if agent_type else current_type

        if username is not None:
            duplicate_agent = await self.mongodb_client.agents.find_one(
                {"username": username, "_id": {"$ne": object_id}}
            )
            if duplicate_agent:
                raise ValueError(f"Agent with username '{username}' already exists")

        update_data = {}
        if username is not None:
            update_data["username"] = username
        if agent_type is not None:
            update_data["type"] = agent_type

        if profile is not None:
            if agent_type is None:
                current_profile = existing_agent.get("profile", {})
                merged_profile = {**current_profile, **profile}
            else:
                merged_profile = profile

            if final_type == "recruiter":
                try:
                    if agent_type is None:
                        UpdateRecruiterProfile(**profile)
                        RecruiterProfile(**merged_profile)
                    else:
                        RecruiterProfile(**merged_profile)
                except Exception as e:
                    raise ValueError(f"Invalid recruiter profile: {str(e)}")
            elif final_type == "candidate":
                try:
                    CandidateProfile(**merged_profile)
                except Exception as e:
                    raise ValueError(f"Invalid candidate profile: {str(e)}")

            update_data["profile"] = merged_profile
            name, bio = self._extract_name_and_bio(merged_profile, final_type)
            update_data["name"] = name
            update_data["bio"] = bio
        elif agent_type is not None:
            name, bio = self._extract_name_and_bio(
                existing_agent.get("profile", {}), final_type
            )
            update_data["name"] = name
            update_data["bio"] = bio

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
            "profile": agent.get("profile", {}),
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

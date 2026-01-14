from datetime import datetime
from typing import Any, AsyncGenerator

from bson import ObjectId
from langchain_google_genai import ChatGoogleGenerativeAI
from src.common.config import settings
from src.common.logger import logger
from src.core.agents.candidate_agent import CandidateAgent
from src.core.agents.orchestrator import ConversationOrchestrator, ConversationTurn
from src.core.agents.recruiter_agent import RecruiterAgent
from src.database.mongodb.mongodb_client import MongoDBClient


class ConversationService:
    def __init__(self, mongodb_client: MongoDBClient):
        self.mongodb_client = mongodb_client
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.8,
        )
        self.active_conversations: dict[str, ConversationOrchestrator] = {}

    async def _get_agent(self, agent_id: str) -> dict[str, Any]:
        try:
            agent = await self.mongodb_client.agents.find_one(
                {"_id": ObjectId(agent_id)}
            )
        except Exception:
            raise ValueError(f"Invalid agent ID format: {agent_id}")

        if not agent:
            raise ValueError(f"Agent with id {agent_id} not found")

        return agent

    async def start_conversation(
        self, recruiter_id: str, candidate_id: str
    ) -> dict[str, Any]:
        recruiter_doc = await self._get_agent(recruiter_id)
        candidate_doc = await self._get_agent(candidate_id)

        if recruiter_doc["type"] != "recruiter":
            raise ValueError(f"Agent {recruiter_id} is not a recruiter")
        if candidate_doc["type"] != "candidate":
            raise ValueError(f"Agent {candidate_id} is not a candidate")

        conversation_doc = {
            "recruiter": {
                "agent_id": recruiter_id,
                "name": recruiter_doc["name"],
            },
            "candidate": {
                "agent_id": candidate_id,
                "name": candidate_doc["name"],
            },
            "messages": [],
            "final_evaluation": "",
            "match_score": None,
            "decision": None,
            "status": "in_progress",
            "created_at": datetime.utcnow(),
            "completed_at": None,
        }

        result = await self.mongodb_client.conversations.insert_one(conversation_doc)
        conversation_id = str(result.inserted_id)

        recruiter_agent = RecruiterAgent(recruiter_doc["profile"], self.llm)
        candidate_agent = CandidateAgent(candidate_doc["profile"], self.llm)
        orchestrator = ConversationOrchestrator(recruiter_agent, candidate_agent)

        self.active_conversations[conversation_id] = orchestrator

        logger.info(
            f"Started conversation {conversation_id} between {recruiter_doc['name']} and {candidate_doc['name']}"
        )

        return {
            "conversation_id": conversation_id,
            "recruiter": {
                "agent_id": recruiter_id,
                "agent_type": "recruiter",
                "name": recruiter_doc["name"],
            },
            "candidate": {
                "agent_id": candidate_id,
                "agent_type": "candidate",
                "name": candidate_doc["name"],
            },
            "status": "in_progress",
            "created_at": conversation_doc["created_at"].isoformat(),
        }

    async def run_conversation_stream(
        self, conversation_id: str, max_turns: int = 12
    ) -> AsyncGenerator[ConversationTurn, None]:
        if conversation_id not in self.active_conversations:
            raise ValueError(f"No active conversation with id {conversation_id}")

        orchestrator = self.active_conversations[conversation_id]
        final_evaluation = ""
        match_score = None
        decision = None

        async for turn in orchestrator.run_conversation_stream(max_turns):
            message_doc = {
                "role": turn.role,
                "speaker_name": turn.speaker_name,
                "content": turn.content,
                "timestamp": turn.timestamp,
            }

            await self.mongodb_client.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$push": {"messages": message_doc}},
            )

            if turn.is_final and turn.final_evaluation:
                final_evaluation = turn.final_evaluation
                match_score, decision = self._parse_evaluation(final_evaluation)

                await self.mongodb_client.conversations.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {
                        "$set": {
                            "final_evaluation": final_evaluation,
                            "match_score": match_score,
                            "decision": decision,
                            "status": "completed",
                            "completed_at": datetime.utcnow(),
                        }
                    },
                )

                if match_score and decision:
                    await self._create_match(
                        conversation_id, match_score, decision, orchestrator
                    )

            yield turn

        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]

        logger.info(f"Conversation {conversation_id} completed")

    def _parse_evaluation(self, evaluation: str) -> tuple[int | None, str | None]:
        score = None
        decision = None

        if "Rating:" in evaluation:
            try:
                rating_part = evaluation.split("Rating:")[1].split("/")[0].strip()
                score = int(rating_part)
            except (IndexError, ValueError):
                pass

        if "GOOD FIT" in evaluation.upper():
            decision = "GOOD FIT"
        elif "NOT A FIT" in evaluation.upper():
            decision = "NOT A FIT"

        return score, decision

    async def _create_match(
        self,
        conversation_id: str,
        score: int,
        decision: str,
        orchestrator: ConversationOrchestrator,
    ):
        conversation = await self.mongodb_client.conversations.find_one(
            {"_id": ObjectId(conversation_id)}
        )

        if not conversation:
            return

        match_doc = {
            "conversation_id": conversation_id,
            "recruiter_id": conversation["recruiter"]["agent_id"],
            "candidate_id": conversation["candidate"]["agent_id"],
            "recruiter_name": orchestrator.recruiter.name,
            "candidate_name": orchestrator.candidate.name,
            "score": score,
            "decision": decision,
            "created_at": datetime.utcnow(),
        }

        await self.mongodb_client.matches.insert_one(match_doc)
        logger.info(
            f"Created match for conversation {conversation_id}: {decision} ({score}/10)"
        )

    async def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        try:
            conversation = await self.mongodb_client.conversations.find_one(
                {"_id": ObjectId(conversation_id)}
            )
        except Exception:
            raise ValueError(f"Invalid conversation ID format: {conversation_id}")

        if not conversation:
            raise ValueError(f"Conversation with id {conversation_id} not found")

        return {
            "conversation_id": str(conversation["_id"]),
            "recruiter": {
                "agent_id": conversation["recruiter"]["agent_id"],
                "agent_type": "recruiter",
                "name": conversation["recruiter"]["name"],
            },
            "candidate": {
                "agent_id": conversation["candidate"]["agent_id"],
                "agent_type": "candidate",
                "name": conversation["candidate"]["name"],
            },
            "messages": conversation["messages"],
            "final_evaluation": conversation["final_evaluation"],
            "match_score": conversation["match_score"],
            "decision": conversation["decision"],
            "status": conversation["status"],
            "created_at": conversation["created_at"].isoformat(),
            "completed_at": (
                conversation["completed_at"].isoformat()
                if conversation["completed_at"]
                else None
            ),
        }

    async def get_all_conversations(self) -> list[dict[str, Any]]:
        cursor = self.mongodb_client.conversations.find().sort("created_at", -1)
        conversations = await cursor.to_list(length=None)

        return [
            {
                "conversation_id": str(conv["_id"]),
                "recruiter_name": conv["recruiter"]["name"],
                "candidate_name": conv["candidate"]["name"],
                "match_score": conv["match_score"],
                "decision": conv["decision"],
                "status": conv["status"],
                "created_at": conv["created_at"].isoformat(),
            }
            for conv in conversations
        ]

    async def get_conversations_for_agent(self, agent_id: str) -> list[dict[str, Any]]:
        cursor = self.mongodb_client.conversations.find(
            {
                "$or": [
                    {"recruiter.agent_id": agent_id},
                    {"candidate.agent_id": agent_id},
                ]
            }
        ).sort("created_at", -1)

        conversations = await cursor.to_list(length=None)

        return [
            {
                "conversation_id": str(conv["_id"]),
                "recruiter_name": conv["recruiter"]["name"],
                "candidate_name": conv["candidate"]["name"],
                "match_score": conv["match_score"],
                "decision": conv["decision"],
                "status": conv["status"],
                "created_at": conv["created_at"].isoformat(),
            }
            for conv in conversations
        ]

    async def get_matches(self, min_score: int | None = None) -> list[dict[str, Any]]:
        query = {}
        if min_score:
            query["score"] = {"$gte": min_score}

        cursor = self.mongodb_client.matches.find(query).sort("created_at", -1)
        matches = await cursor.to_list(length=None)

        return [
            {
                "match_id": str(match["_id"]),
                "conversation_id": match["conversation_id"],
                "recruiter_id": match["recruiter_id"],
                "candidate_id": match["candidate_id"],
                "recruiter_name": match["recruiter_name"],
                "candidate_name": match["candidate_name"],
                "score": match["score"],
                "decision": match["decision"],
                "created_at": match["created_at"].isoformat(),
            }
            for match in matches
        ]

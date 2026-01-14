import asyncio
import math
import random
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Callable, Optional

from bson import ObjectId
from src.common.logger import logger
from src.database.mongodb.mongodb_client import MongoDBClient
from src.module.conversation.conversation_service import ConversationService


@dataclass
class AgentState:
    agent_id: str
    name: str
    agent_type: str
    x: float
    y: float
    state: str = "idle"
    conversation_with: Optional[str] = None
    target_x: Optional[float] = None
    target_y: Optional[float] = None
    idle_time: float = 0.0


@dataclass
class WorldConfig:
    proximity_threshold: float = 50.0
    move_speed: float = 2.0
    world_width: int = 800
    world_height: int = 600
    update_interval: float = 0.1
    idle_duration_min: float = 2.0
    idle_duration_max: float = 5.0


class WorldService:
    def __init__(
        self,
        mongodb_client: MongoDBClient,
        conversation_service: ConversationService,
    ):
        self.mongodb_client = mongodb_client
        self.conversation_service = conversation_service
        self.config = WorldConfig()
        self.agents: dict[str, AgentState] = {}
        self.active_conversations: dict[str, dict[str, Any]] = {}
        self.running = False
        self._update_task: Optional[asyncio.Task] = None
        self._state_callbacks: list[Callable] = []
        self._conversation_started_pairs: set[tuple[str, str]] = set()

    async def spawn_agent(
        self, agent_id: str, x: Optional[float] = None, y: Optional[float] = None
    ) -> AgentState:
        if agent_id in self.agents:
            return self.agents[agent_id]

        try:
            agent = await self.mongodb_client.agents.find_one(
                {"_id": ObjectId(agent_id)}
            )
        except Exception:
            raise ValueError(f"Invalid agent ID format: {agent_id}")

        if not agent:
            raise ValueError(f"Agent with id {agent_id} not found")

        spawn_x = (
            x if x is not None else random.uniform(50, self.config.world_width - 50)
        )
        spawn_y = (
            y if y is not None else random.uniform(50, self.config.world_height - 50)
        )

        agent_state = AgentState(
            agent_id=agent_id,
            name=agent["name"],
            agent_type=agent["type"],
            x=spawn_x,
            y=spawn_y,
            state="idle",
        )

        self.agents[agent_id] = agent_state
        logger.info(f"Spawned agent {agent['name']} at ({spawn_x:.1f}, {spawn_y:.1f})")

        return agent_state

    def remove_agent(self, agent_id: str) -> bool:
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]

        if agent.conversation_with:
            partner_id = agent.conversation_with
            if partner_id in self.agents:
                partner = self.agents[partner_id]
                partner.state = "idle"
                partner.conversation_with = None

        del self.agents[agent_id]
        logger.info(f"Removed agent {agent_id}")
        return True

    def get_world_state(self) -> dict[str, Any]:
        return {
            "agents": [
                {
                    "agent_id": a.agent_id,
                    "name": a.name,
                    "agent_type": a.agent_type,
                    "x": a.x,
                    "y": a.y,
                    "state": a.state,
                    "conversation_with": a.conversation_with,
                }
                for a in self.agents.values()
            ],
            "active_conversations": list(self.active_conversations.values()),
            "world_width": self.config.world_width,
            "world_height": self.config.world_height,
        }

    def _distance(self, a1: AgentState, a2: AgentState) -> float:
        return math.sqrt((a1.x - a2.x) ** 2 + (a1.y - a2.y) ** 2)

    def _set_random_target(self, agent: AgentState):
        agent.target_x = random.uniform(50, self.config.world_width - 50)
        agent.target_y = random.uniform(50, self.config.world_height - 50)

    def _update_position(self, agent: AgentState, dt: float):
        if agent.state == "talking":
            return

        if agent.state == "idle":
            agent.idle_time += dt
            idle_duration = random.uniform(
                self.config.idle_duration_min, self.config.idle_duration_max
            )
            if agent.idle_time >= idle_duration:
                agent.state = "walking"
                agent.idle_time = 0.0
                self._set_random_target(agent)
            return

        if agent.target_x is None or agent.target_y is None:
            self._set_random_target(agent)
            return

        dx = agent.target_x - agent.x
        dy = agent.target_y - agent.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 5:
            agent.state = "idle"
            agent.target_x = None
            agent.target_y = None
            return

        move_dist = self.config.move_speed * dt * 60
        if move_dist > dist:
            move_dist = dist

        agent.x += (dx / dist) * move_dist
        agent.y += (dy / dist) * move_dist

        agent.x = max(20, min(self.config.world_width - 20, agent.x))
        agent.y = max(20, min(self.config.world_height - 20, agent.y))

    async def _check_proximity_and_start_conversations(self):
        agent_list = list(self.agents.values())

        for i, a1 in enumerate(agent_list):
            if a1.state == "talking":
                continue

            for a2 in agent_list[i + 1 :]:
                if a2.state == "talking":
                    continue

                if a1.agent_type == a2.agent_type:
                    continue

                pair = tuple(sorted([a1.agent_id, a2.agent_id]))
                if pair in self._conversation_started_pairs:
                    continue

                dist = self._distance(a1, a2)
                if dist <= self.config.proximity_threshold:
                    recruiter = a1 if a1.agent_type == "recruiter" else a2
                    candidate = a2 if a1.agent_type == "recruiter" else a1

                    self._conversation_started_pairs.add(pair)

                    await self._start_conversation(recruiter, candidate)

    async def _start_conversation(self, recruiter: AgentState, candidate: AgentState):
        recruiter.state = "talking"
        recruiter.conversation_with = candidate.agent_id
        candidate.state = "talking"
        candidate.conversation_with = recruiter.agent_id

        try:
            result = await self.conversation_service.start_conversation(
                recruiter_id=recruiter.agent_id,
                candidate_id=candidate.agent_id,
            )

            conversation_id = result["conversation_id"]

            self.active_conversations[conversation_id] = {
                "conversation_id": conversation_id,
                "recruiter_id": recruiter.agent_id,
                "candidate_id": candidate.agent_id,
                "recruiter_name": recruiter.name,
                "candidate_name": candidate.name,
            }

            logger.info(
                f"Started conversation {conversation_id} between {recruiter.name} and {candidate.name}"
            )

            asyncio.create_task(
                self._run_conversation(conversation_id, recruiter, candidate)
            )

        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            recruiter.state = "idle"
            recruiter.conversation_with = None
            candidate.state = "idle"
            candidate.conversation_with = None

    async def _run_conversation(
        self,
        conversation_id: str,
        recruiter: AgentState,
        candidate: AgentState,
    ):
        try:
            async for turn in self.conversation_service.run_conversation_stream(
                conversation_id
            ):
                for callback in self._state_callbacks:
                    await callback(
                        {
                            "type": "conversation_turn",
                            "conversation_id": conversation_id,
                            "turn": {
                                "role": turn.role,
                                "speaker_name": turn.speaker_name,
                                "content": turn.content,
                                "timestamp": turn.timestamp,
                                "is_final": turn.is_final,
                                "final_evaluation": turn.final_evaluation,
                            },
                        }
                    )

            logger.info(f"Conversation {conversation_id} completed")

        except Exception as e:
            logger.error(f"Conversation {conversation_id} failed: {e}")

        finally:
            if recruiter.agent_id in self.agents:
                self.agents[recruiter.agent_id].state = "idle"
                self.agents[recruiter.agent_id].conversation_with = None

            if candidate.agent_id in self.agents:
                self.agents[candidate.agent_id].state = "idle"
                self.agents[candidate.agent_id].conversation_with = None

            if conversation_id in self.active_conversations:
                del self.active_conversations[conversation_id]

    async def _update_loop(self):
        last_time = asyncio.get_event_loop().time()

        while self.running:
            current_time = asyncio.get_event_loop().time()
            dt = current_time - last_time
            last_time = current_time

            for agent in self.agents.values():
                self._update_position(agent, dt)

            await self._check_proximity_and_start_conversations()

            for callback in self._state_callbacks:
                await callback({"type": "world_state", "data": self.get_world_state()})

            await asyncio.sleep(self.config.update_interval)

    def start(self):
        if self.running:
            return

        self.running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("World simulation started")

    def stop(self):
        self.running = False
        if self._update_task:
            self._update_task.cancel()
            self._update_task = None
        logger.info("World simulation stopped")

    def add_state_callback(self, callback: Callable):
        self._state_callbacks.append(callback)

    def remove_state_callback(self, callback: Callable):
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    async def stream_world_state(self) -> AsyncGenerator[dict[str, Any], None]:
        queue: asyncio.Queue = asyncio.Queue()

        async def callback(state: dict):
            await queue.put(state)

        self.add_state_callback(callback)

        try:
            while self.running:
                state = await queue.get()
                yield state
        finally:
            self.remove_state_callback(callback)

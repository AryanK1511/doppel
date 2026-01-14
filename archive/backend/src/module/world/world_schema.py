from typing import Literal, Optional

from pydantic import BaseModel, Field


class Position(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class AgentPosition(BaseModel):
    agent_id: str = Field(..., description="Agent document ID")
    name: str = Field(..., description="Agent name")
    agent_type: Literal["recruiter", "candidate"] = Field(..., description="Agent type")
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    state: Literal["idle", "walking", "talking"] = Field(
        "idle", description="Current agent state"
    )
    conversation_with: Optional[str] = Field(
        None, description="Agent ID of conversation partner if talking"
    )


class ActiveConversation(BaseModel):
    conversation_id: str = Field(..., description="Conversation document ID")
    recruiter_id: str = Field(..., description="Recruiter agent ID")
    candidate_id: str = Field(..., description="Candidate agent ID")
    recruiter_name: str = Field(..., description="Recruiter name")
    candidate_name: str = Field(..., description="Candidate name")


class WorldState(BaseModel):
    agents: list[AgentPosition] = Field(..., description="All agent positions")
    active_conversations: list[ActiveConversation] = Field(
        ..., description="Currently active conversations"
    )
    world_width: int = Field(800, description="World width in pixels")
    world_height: int = Field(600, description="World height in pixels")


class SpawnAgentRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID to spawn")
    x: Optional[float] = Field(None, description="Optional X coordinate")
    y: Optional[float] = Field(None, description="Optional Y coordinate")


class RemoveAgentRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID to remove")


class WorldConfig(BaseModel):
    proximity_threshold: float = Field(
        50.0, description="Distance threshold to trigger conversation"
    )
    move_speed: float = Field(2.0, description="Agent movement speed")
    world_width: int = Field(800, description="World width in pixels")
    world_height: int = Field(600, description="World height in pixels")
    update_interval: float = Field(0.1, description="World update interval in seconds")

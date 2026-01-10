from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreateAgentRequest(BaseModel):
    username: str = Field(..., description="Agent username")
    name: str = Field(..., description="Agent name")
    bio: str = Field(..., description="Agent bio")
    type: Literal["candidate", "recruiter"] = Field(..., description="Agent type")


class UpdateAgentRequest(BaseModel):
    username: Optional[str] = Field(None, description="Agent username")
    name: Optional[str] = Field(None, description="Agent name")
    bio: Optional[str] = Field(None, description="Agent bio")
    type: Optional[Literal["candidate", "recruiter"]] = Field(
        None, description="Agent type"
    )


class AgentListItem(BaseModel):
    agent_id: str = Field(..., description="Agent document ID")
    username: str = Field(..., description="Agent username")
    name: str = Field(..., description="Agent name")
    bio: str = Field(..., description="Agent bio")
    type: str = Field(..., description="Agent type")
    created_at: str = Field(..., description="ISO format timestamp of creation")


class AgentResponse(BaseModel):
    agent_id: str = Field(..., description="Agent document ID")
    username: str = Field(..., description="Agent username")
    name: str = Field(..., description="Agent name")
    bio: str = Field(..., description="Agent bio")
    type: str = Field(..., description="Agent type")
    created_at: str = Field(..., description="ISO format timestamp of creation")

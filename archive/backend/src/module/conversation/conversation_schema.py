from typing import Literal, Optional

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["recruiter", "candidate", "system"] = Field(
        ..., description="Role of the speaker"
    )
    speaker_name: str = Field(..., description="Name of the speaker")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO format timestamp")


class ConversationParticipant(BaseModel):
    agent_id: str = Field(..., description="Agent document ID")
    agent_type: Literal["recruiter", "candidate"] = Field(..., description="Agent type")
    name: str = Field(..., description="Agent name")


class StartConversationRequest(BaseModel):
    recruiter_id: str = Field(..., description="Recruiter agent ID")
    candidate_id: str = Field(..., description="Candidate agent ID")


class ConversationTurnResponse(BaseModel):
    role: Literal["recruiter", "candidate"] = Field(..., description="Speaker role")
    speaker_name: str = Field(..., description="Speaker name")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO format timestamp")
    is_final: bool = Field(False, description="Whether this is the final turn")
    final_evaluation: Optional[str] = Field(
        None, description="Final evaluation if is_final"
    )


class ConversationResult(BaseModel):
    conversation_id: str = Field(..., description="Conversation document ID")
    recruiter: ConversationParticipant = Field(..., description="Recruiter participant")
    candidate: ConversationParticipant = Field(..., description="Candidate participant")
    messages: list[ConversationMessage] = Field(
        ..., description="Conversation messages"
    )
    final_evaluation: str = Field(..., description="Final evaluation from recruiter")
    match_score: Optional[int] = Field(None, description="Match score 1-10")
    decision: Optional[str] = Field(None, description="GOOD FIT or NOT A FIT")
    status: Literal["in_progress", "completed"] = Field(
        ..., description="Conversation status"
    )
    created_at: str = Field(..., description="ISO format timestamp")
    completed_at: Optional[str] = Field(
        None, description="ISO format timestamp of completion"
    )


class ConversationListItem(BaseModel):
    conversation_id: str = Field(..., description="Conversation document ID")
    recruiter_name: str = Field(..., description="Recruiter name")
    candidate_name: str = Field(..., description="Candidate name")
    match_score: Optional[int] = Field(None, description="Match score 1-10")
    decision: Optional[str] = Field(None, description="GOOD FIT or NOT A FIT")
    status: str = Field(..., description="Conversation status")
    created_at: str = Field(..., description="ISO format timestamp")


class MatchResult(BaseModel):
    match_id: str = Field(..., description="Match document ID")
    conversation_id: str = Field(..., description="Related conversation ID")
    recruiter_id: str = Field(..., description="Recruiter agent ID")
    candidate_id: str = Field(..., description="Candidate agent ID")
    recruiter_name: str = Field(..., description="Recruiter name")
    candidate_name: str = Field(..., description="Candidate name")
    score: int = Field(..., description="Match score 1-10")
    decision: str = Field(..., description="GOOD FIT or NOT A FIT")
    created_at: str = Field(..., description="ISO format timestamp")

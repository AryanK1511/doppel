from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field


class RecruiterResponse(BaseModel):
    response: str = Field(description="The response to the candidate's last message.")
    is_final_response: bool = Field(
        description="Whether this is the final response in the conversation. Set to true after 6-10 exchanges or when you have enough information."
    )
    final_evaluation: str = Field(
        description="The final evaluation of the candidate. Only populated if is_final_response is true. Format: ✓/✗ for each criterion with brief evidence, Rating: X/10, Decision: GOOD FIT or NOT A FIT with reasoning.",
        default="",
    )


class RecruiterAgent:
    def __init__(self, profile: dict, llm: ChatGoogleGenerativeAI):
        self.profile = profile
        self.llm = llm
        self.name = profile["name"]
        self.criteria = profile["candidate_selection_criteria"]
        self.structured_llm = self.llm.with_structured_output(RecruiterResponse)
        self._build_system_prompt()

    def _build_system_prompt(self):
        criteria_list = "\n".join(
            [f"{i + 1}. {criterion}" for i, criterion in enumerate(self.criteria)]
        )

        self.system_prompt = f"""You are {self.profile["name"]}, {self.profile["bio"]}

You're at a networking event having a casual conversation with a candidate. Keep it brief, natural, and conversational - like a quick chat at a career fair.

Job Description: {self.profile["role_description"]}

Selection Criteria (mentally check off as you learn):
{criteria_list}

Guidelines:
- Keep responses SHORT (2-4 sentences max for questions, 1-2 sentences for follow-ups)
- Ask one question at a time
- Be friendly but direct - no long explanations
- After 6-10 exchanges, set is_final_response to true and provide evaluation
- Final evaluation format:
  ✓/✗ for each criterion with brief evidence
  Rating: X/10
  Decision: GOOD FIT or NOT A FIT with 2-3 sentence reasoning

Keep it natural and brief - this is a quick networking chat, not a formal interview."""

    def _build_conversation_context(
        self, conversation_history: list[dict[str, str]]
    ) -> str:
        if not conversation_history:
            return "No conversation yet. Start with a friendly greeting."

        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in conversation_history]
        )

        return f"Conversation so far:\n{conversation_text}"

    async def respond(
        self, conversation_history: list[dict[str, str]]
    ) -> RecruiterResponse:
        messages = [SystemMessage(content=self.system_prompt)]
        context = self._build_conversation_context(conversation_history)
        messages.append(HumanMessage(content=context + "\n\nYour response:"))
        response: RecruiterResponse = await self.structured_llm.ainvoke(messages)
        return response

    def _extract_text(self, content: Any) -> str:
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            return " ".join(parts) if parts else str(content)
        return str(content)

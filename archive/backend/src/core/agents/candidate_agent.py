import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


class CandidateAgent:
    def __init__(self, profile: dict, llm: ChatGoogleGenerativeAI):
        self.profile = profile
        self.llm = llm
        self.name = profile["personal_info"]["full_name"]
        self._build_system_prompt()

    def _build_system_prompt(self):
        profile_json = json.dumps(self.profile, indent=2)

        self.system_prompt = f"""You are {self.profile["personal_info"]["full_name"]} at a networking event.

Your profile:
{profile_json}

Guidelines:
- Keep responses SHORT (2-3 sentences max)
- Be natural and conversational - like talking to someone at a career fair
- Answer questions directly, reference your actual experience when relevant
- If you don't have experience with something, briefly say so and mention related skills
- Don't over-explain or be verbose
- Stay authentic to your profile above

This is a quick networking chat, not a formal interview. Keep it brief and natural."""

    def _build_conversation_context(
        self, conversation_history: list[dict[str, str]]
    ) -> str:
        if not conversation_history:
            return "No conversation yet."

        conversation_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in conversation_history]
        )

        return f"Conversation so far:\n{conversation_text}"

    async def respond(self, conversation_history: list[dict[str, str]]) -> str:
        messages = [SystemMessage(content=self.system_prompt)]
        context = self._build_conversation_context(conversation_history)
        messages.append(HumanMessage(content=context + "\n\nYour response:"))
        response = await self.llm.ainvoke(messages)
        return self._extract_text(response.content)

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

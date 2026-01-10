from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import TextPart
from a2a.utils import new_agent_text_message
from ai.agent import ScriptGeneratorAgent
from common.logger import logger


class ScriptGeneratorAgentExecutor:
    def __init__(self, agent: ScriptGeneratorAgent):
        self.agent = agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> str:
        user_message = ""
        if context.message and context.message.parts:
            text_parts = [
                part.root
                for part in context.message.parts
                if isinstance(part.root, TextPart)
            ]
            if text_parts:
                user_message = " ".join(part.text for part in text_parts)

        if not user_message:
            user_message = "Help me create a script"

        logger.info(f"User message: {user_message}")

        result = await self.agent.invoke(user_message)
        await event_queue.enqueue_event(new_agent_text_message(result))
        return result

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Cancel not supported")

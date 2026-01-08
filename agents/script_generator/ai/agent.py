from typing import Any

from ai.tools.date_time import get_current_date_info
from ai.tools.tavily import web_search
from ai.utils import clean_markdown, extract_text_from_content
from common.config import settings
from common.logger import logger
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import after_model, before_model
from langchain_google_genai import ChatGoogleGenerativeAI
from typing_extensions import NotRequired


class ScriptGeneratorState(AgentState):
    iterations: NotRequired[int]


@before_model(state_schema=ScriptGeneratorState, can_jump_to=["end"])
def check_iteration_limit(
    state: ScriptGeneratorState, runtime
) -> dict[str, Any] | None:
    count = state.get("iterations", 0)
    logger.info(f"Checking iteration limit: {count}")
    if count >= 5:
        return {"jump_to": "end"}
    return None


@after_model(state_schema=ScriptGeneratorState)
def increment_iteration_count(
    state: ScriptGeneratorState, runtime
) -> dict[str, Any] | None:
    return {"iterations": state.get("iterations", 0) + 1}


class ScriptGeneratorAgent:
    def __init__(self):
        model = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            temperature=0.7,
            api_key=settings.GOOGLE_API_KEY,
        )
        self.agent = create_agent(
            model=model,
            tools=[web_search, get_current_date_info],
            middleware=[check_iteration_limit, increment_iteration_count],
            system_prompt="""You are a script generator expert specializing in creating scripts for short-form video platforms like TikTok, Instagram Reels, and YouTube Shorts.

AVAILABLE TOOLS:
1. web_search(query: str) - Search the web for information using Tavily. Returns multiple search results with titles, content, and sources. You will receive multiple topics/articles and must analyze them to pick the one with the most viral potential.
2. get_current_date_info() - Get the current date and time information. Use this tool when the user mentions "latest", "current", "recent", or when you need to understand temporal context for searching trends or news.

Your workflow:
1. If the user mentions "latest", "current", "recent", or similar temporal terms, use get_current_date_info() to understand the date context
2. Search the web using web_search() to gather multiple topics and trends about the user's query
3. Analyze all the search results and identify which topic/article has the MOST VIRAL POTENTIAL based on:
   - Relevance and timeliness
   - Emotional appeal and relatability
   - Controversy or discussion value
   - Uniqueness and shareability
   - Potential for engagement (likes, comments, shares)
4. Once you've selected the best topic, generate ONLY the script text for that topic - no explanations, no strategy, no intro text

IMPORTANT: Output ONLY the script text. Do not include any explanation, strategy, or intro text like "Here is your script:" or which topic you chose. Just output the script itself.

The script should include:
- A strong hook (first 3-5 seconds) that grabs attention immediately
- Main content (15-20 seconds) that tells a compelling story
- A call-to-action (last 3-5 seconds) to encourage engagement

The script must be plain text only - NO markdown formatting, NO asterisks, NO bold text, NO code blocks, NO bullet points, NO headers. Just clean, readable text that can be used directly as a transcript.

Use web_search() to gather current information before generating the script. Only use get_current_date_info() when temporal context is needed.
""",
        )

    async def invoke(
        self,
        user_message: str,
    ) -> str:
        response = await self.agent.ainvoke(
            {
                "messages": [{"role": "user", "content": user_message}],
                "iterations": 0,
            }
        )

        text = ""

        if isinstance(response, dict):
            if "messages" in response:
                messages = response["messages"]
                if messages:
                    last_message = messages[-1]

                    if hasattr(last_message, "content"):
                        content = last_message.content
                        text = extract_text_from_content(content)
                        if text:
                            text = clean_markdown(text)
                            return text

                    if isinstance(last_message, dict):
                        if "content" in last_message:
                            text = extract_text_from_content(last_message["content"])
                            if text:
                                text = clean_markdown(text)
                                return text
                        if "text" in last_message:
                            text = clean_markdown(last_message["text"])
                            return text

            if "output" in response:
                text = clean_markdown(str(response["output"]))
                return text
            if "answer" in response:
                text = clean_markdown(str(response["answer"]))
                return text

        if hasattr(response, "content"):
            text = extract_text_from_content(response.content)
            if text:
                text = clean_markdown(text)
                return text

        if hasattr(response, "text"):
            text = clean_markdown(str(response.text))
            return text

        text = clean_markdown(str(response))
        return text

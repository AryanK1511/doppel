from abc import ABC, abstractmethod
from typing import List, Optional

from google import genai
from pydantic import BaseModel, Field
from src.common.config import settings
from src.common.logger import logger
from tavily import TavilyClient


class ViralArticle(BaseModel):
    title: str = Field(..., description="The title of the chosen article")
    content: str = Field(..., description="The full content of the chosen article")
    reason: str = Field(
        ..., description="Explanation of why this article has the most viral potential"
    )


class ReelScript(BaseModel):
    hook: str = Field(
        ...,
        description="The opening hook (first 3-5 seconds) that grabs attention immediately",
    )
    main_content: str = Field(
        ..., description="The main story/content for the middle section (15-20 seconds)"
    )
    call_to_action: str = Field(
        ...,
        description="The closing call-to-action to encourage engagement (last 3-5 seconds)",
    )
    asset_prompts: List[str] = Field(
        ..., description="List of prompts for images/videos needed for the reel"
    )


class Command(ABC):
    @abstractmethod
    def execute(self, context: dict) -> dict:
        pass


class SearchLatestNewsCommand(Command):
    def __init__(self, agent: "ReelsAgent"):
        self.agent = agent

    def execute(self, context: dict) -> dict:
        initial_topic = context.get("initial_topic")
        articles = self.agent.search_latest_news(initial_topic)
        context["articles"] = articles
        logger.info(f"Command 1/4 completed: Found {len(articles)} articles")
        return context


class FindViralTopicCommand(Command):
    def __init__(self, agent: "ReelsAgent"):
        self.agent = agent

    def execute(self, context: dict) -> dict:
        articles = context.get("articles", [])
        category = context.get("category")
        selected_topic = self.agent.find_viral_topic(articles, category)
        context["selected_topic"] = selected_topic
        logger.info(
            f"Command 2/4 completed: Selected topic - {selected_topic['title']}"
        )
        return context


class ResearchTopicCommand(Command):
    def __init__(self, agent: "ReelsAgent"):
        self.agent = agent

    def execute(self, context: dict) -> dict:
        selected_topic = context.get("selected_topic", {})
        topic_title = selected_topic.get("title", "")
        research = self.agent.research_topic(topic_title)
        context["research"] = research
        logger.info(
            f"Command 3/4 completed: Completed research with {len(research)} articles"
        )
        return context


class GenerateScriptCommand(Command):
    def __init__(self, agent: "ReelsAgent"):
        self.agent = agent

    def execute(self, context: dict) -> dict:
        selected_topic = context.get("selected_topic", {})
        research = context.get("research", [])
        script_output = self.agent.generate_script_and_prompts(selected_topic, research)
        context["script"] = script_output
        logger.info("Command 4/4 completed: Generated script and asset prompts")
        return context


class ReelsAgent:
    def __init__(self):
        self.tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        self.genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.command_queue: List[Command] = []

    def search_latest_news(self, topic: str) -> List[dict]:
        logger.info(f"Starting web search for latest news on topic: {topic}")
        try:
            response = self.tavily_client.search(
                query=topic,
                include_answer="basic",
                topic="news",
                search_depth="basic",
                max_results=5,
            )

            news_articles = [
                {
                    "title": article.get("title", ""),
                    "content": article.get("content", ""),
                }
                for article in response.get("results", [])
            ]

            logger.info(
                f"Web search completed. Found {len(news_articles)} articles for topic: {topic}"
            )
            return news_articles
        except Exception as e:
            logger.error(f"Error during web search for topic '{topic}': {str(e)}")
            raise

    def find_viral_topic(
        self, articles: List[dict], category: Optional[str] = None
    ) -> dict:
        logger.info(
            f"Starting viral topic selection. Analyzing {len(articles)} articles"
            + (f" in category: {category}" if category else "")
        )
        try:
            category_context = f"Focus on the {category} category. " if category else ""

            system_prompt = """You are a news article analyzer specialized in identifying content with maximum viral potential for short-form video platforms like Instagram Reels and TikTok.

Analyze the given articles and select the one that has the highest potential to go viral. Consider:
- Emotional resonance and relatability
- Controversy or debate potential
- Timeliness and relevance
- Surprise factor or unexpected angles
- Visual storytelling potential
- Shareability and discussion value

Return your selection as JSON with 'title', 'content', and 'reason' fields."""

            articles_text = "\n\n".join(
                [
                    f"Article {i + 1}:\nTitle: {article.get('title', '')}\nContent: {article.get('content', '')[:500]}"
                    for i, article in enumerate(articles)
                ]
            )

            user_prompt = f"""{category_context}Here are the news articles to analyze:

{articles_text}

Select the article with the most viral potential and explain why."""

            full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn your response as valid JSON matching this schema: {ViralArticle.model_json_schema()}"

            response = self.genai_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=full_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                },
            )

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            viral_article = ViralArticle.model_validate_json(response_text)
            selected_topic = {
                "title": viral_article.title,
                "content": viral_article.content,
                "reason": viral_article.reason,
            }

            logger.info(
                f"Viral topic selected: {selected_topic['title']}. Reason: {selected_topic['reason'][:100]}..."
            )
            return selected_topic
        except Exception as e:
            logger.error(f"Error during viral topic selection: {str(e)}")
            raise

    def research_topic(self, topic: str) -> List[dict]:
        logger.info(f"Starting deep research on topic: {topic}")
        try:
            research_query = f"Latest news and updates about: {topic}"

            response = self.tavily_client.search(
                query=research_query,
                include_answer="basic",
                topic="news",
                search_depth="advanced",
                max_results=5,
            )

            research_articles = [
                {
                    "title": article.get("title", ""),
                    "content": article.get("content", ""),
                }
                for article in response.get("results", [])
            ]

            logger.info(
                f"Deep research completed. Found {len(research_articles)} research articles for topic: {topic}"
            )
            return research_articles
        except Exception as e:
            logger.error(f"Error during deep research on topic '{topic}': {str(e)}")
            raise

    def generate_script_and_prompts(
        self, selected_topic: dict, research: List[dict]
    ) -> dict:
        logger.info(
            f"Starting script generation for topic: {selected_topic.get('title', '')}"
        )
        try:
            system_prompt = """You are a viral short-form video script writer. You create engaging, attention-grabbing scripts for 30-second videos (Instagram Reels, TikTok) that maximize views, likes, and shares.

Your scripts must:
- Start with a strong hook in the first 3-5 seconds that immediately grabs attention
- Tell a compelling story in 15-20 seconds with clear narrative flow
- End with a clear call-to-action in the last 3-5 seconds to encourage engagement
- Be optimized for short-form video algorithms (trending sounds, hashtags, engagement triggers)
- Use conversational, relatable language that resonates with viewers
- Include specific visual prompts for images/videos that enhance the narrative

Return your script as JSON with 'hook', 'main_content', 'call_to_action', and 'asset_prompts' fields. The asset_prompts should be a list of detailed prompts for each visual asset needed."""

            research_context = ""
            if research:
                research_context = "\n\nAdditional research context:\n"
                for article in research:
                    research_context += (
                        f"- {article['title']}: {article['content'][:200]}...\n"
                    )

            user_prompt = f"""Based on this news article and additional research, create a viral short-form video script for a 30-second reel:

Title: {selected_topic["title"]}
Content: {selected_topic["content"]}
Reason for viral potential: {selected_topic["reason"]}
{research_context}

Generate a script that will maximize engagement and go viral. Include specific prompts for all visual assets needed."""

            full_prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn your response as valid JSON matching this schema: {ReelScript.model_json_schema()}"

            response = self.genai_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=full_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                },
            )

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            reel_script = ReelScript.model_validate_json(response_text)
            script_output = {
                "hook": reel_script.hook,
                "main_content": reel_script.main_content,
                "call_to_action": reel_script.call_to_action,
                "asset_prompts": reel_script.asset_prompts,
            }

            logger.info(
                f"Script generation completed. Hook: {script_output['hook'][:50]}... | Asset prompts: {len(script_output['asset_prompts'])}"
            )
            return script_output
        except Exception as e:
            logger.error(f"Error during script generation: {str(e)}")
            raise

    def run(self, initial_topic: str, category: Optional[str] = None) -> dict:
        logger.info(
            f"Starting ReelsAgent pipeline with initial topic: {initial_topic}"
            + (f" in category: {category}" if category else "")
        )
        try:
            self.command_queue = [
                SearchLatestNewsCommand(self),
                FindViralTopicCommand(self),
                ResearchTopicCommand(self),
                GenerateScriptCommand(self),
            ]

            context = {
                "initial_topic": initial_topic,
                "category": category,
            }

            for command in self.command_queue:
                context = command.execute(context)

            result = {
                "initial_topic": context.get("initial_topic"),
                "category": context.get("category"),
                "articles": context.get("articles", []),
                "selected_topic": context.get("selected_topic", {}),
                "research": context.get("research", []),
                "script": context.get("script", {}),
            }

            script_output = result.get("script", {})
            logger.info(
                f"ReelsAgent pipeline completed successfully. Final script hook: {script_output.get('hook', '')[:50]}..."
            )
            return result
        except Exception as e:
            logger.error(f"Error in ReelsAgent pipeline: {str(e)}")
            raise

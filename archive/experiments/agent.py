import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field
from tavily import TavilyClient

load_dotenv()


class State(TypedDict):
    search_query: str
    initial_articles: list[dict]
    selected_article: dict
    additional_research: list[dict]
    final_script: dict


class ViralArticle(BaseModel):
    title: str = Field(..., description="The title of the chosen article")
    content: str = Field(..., description="The full content of the chosen article")
    reason: str = Field(
        ..., description="Explanation of why this article has the most viral potential"
    )


class TikTokScript(BaseModel):
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


def web_search(state: State) -> State:
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")

    client = TavilyClient(api_key=tavily_api_key)
    query = state.get("search_query", "What is the latest news on AI?")

    response = client.search(
        query=query,
        include_answer="basic",
        topic="news",
        search_depth="basic",
        max_results=3,
    )

    news_articles = [
        {"title": article.get("title", ""), "content": article.get("content", "")}
        for article in response.get("results", [])
    ]

    return {"initial_articles": news_articles}


def select_article(state: State) -> State:
    model = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview", api_key=os.getenv("GEMINI_API_KEY")
    )
    model_with_structure = model.with_structured_output(ViralArticle)

    article_chooser_system_prompt = """
You are a news article chooser. You are given a list of news articles and you need to choose the one that has the most potential to create the most viral tiktok.
"""

    news_articles = state["initial_articles"]
    article_chooser_user_prompt = f"""
Here are the news articles:
{news_articles}
"""

    messages = [
        {"role": "system", "content": article_chooser_system_prompt},
        {"role": "user", "content": article_chooser_user_prompt},
    ]

    response = model_with_structure.invoke(messages)
    selected_article = {
        "title": response.title,
        "content": response.content,
        "reason": response.reason,
    }

    return {"selected_article": selected_article}


def deep_research(state: State) -> State:
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")

    client = TavilyClient(api_key=tavily_api_key)
    selected_article = state["selected_article"]

    research_query = f"Latest news and updates about: {selected_article['title']}"

    response = client.search(
        query=research_query,
        include_answer="basic",
        topic="news",
        search_depth="advanced",
        max_results=5,
    )

    additional_articles = [
        {"title": article.get("title", ""), "content": article.get("content", "")}
        for article in response.get("results", [])
    ]

    return {"additional_research": additional_articles}


def generate_script(state: State) -> State:
    model = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview", api_key=os.getenv("GEMINI_API_KEY")
    )
    model_with_structure = model.with_structured_output(TikTokScript)

    script_generator_system_prompt = """
You are a viral TikTok script writer. You create engaging, attention-grabbing scripts for 30-second videos that maximize views, likes, and shares.

Your scripts must:
- Start with a strong hook in the first 3-5 seconds
- Tell a compelling story in 15-20 seconds
- End with a clear call-to-action in the last 3-5 seconds
- Be optimized for TikTok's algorithm (trending sounds, hashtags, engagement triggers)
- Use conversational, relatable language
- Include visual suggestions that enhance the narrative
"""

    selected_article = state["selected_article"]
    additional_research = state.get("additional_research", [])

    research_context = "\n\nAdditional research:\n"
    for article in additional_research:
        research_context += f"- {article['title']}: {article['content'][:200]}...\n"

    script_generator_user_prompt = f"""
Based on this news article and additional research, create a viral TikTok script for a 30-second video:

Title: {selected_article["title"]}
Content: {selected_article["content"]}
Reason for viral potential: {selected_article["reason"]}
{research_context}

Generate a script that will maximize engagement and go viral.
"""

    messages = [
        {"role": "system", "content": script_generator_system_prompt},
        {"role": "user", "content": script_generator_user_prompt},
    ]

    script_response = model_with_structure.invoke(messages)
    final_script = {
        "hook": script_response.hook,
        "main_content": script_response.main_content,
        "call_to_action": script_response.call_to_action,
        "visual_notes": script_response.visual_notes,
    }

    return {"final_script": final_script}


def create_agent():
    workflow = StateGraph(State)

    workflow.add_node("web_search", web_search)
    workflow.add_node("select_article", select_article)
    workflow.add_node("deep_research", deep_research)
    workflow.add_node("generate_script", generate_script)

    workflow.set_entry_point("web_search")
    workflow.add_edge("web_search", "select_article")
    workflow.add_edge("select_article", "deep_research")
    workflow.add_edge("deep_research", "generate_script")
    workflow.add_edge("generate_script", END)

    return workflow.compile()


if __name__ == "__main__":
    agent = create_agent()

    initial_state = {
        "search_query": "What is the latest news on AI?",
        "initial_articles": [],
        "selected_article": {},
        "additional_research": [],
        "final_script": {},
    }

    result = agent.invoke(initial_state)

    print("\n" + "=" * 50)
    print("FINAL TIKTOK SCRIPT")
    print("=" * 50)
    print(f"\nHook: {result['final_script']['hook']}")
    print(f"\nMain Content: {result['final_script']['main_content']}")
    print(f"\nCall to Action: {result['final_script']['call_to_action']}")
    print(f"\nVisual Notes: {result['final_script']['visual_notes']}")
    print("\n" + "=" * 50)

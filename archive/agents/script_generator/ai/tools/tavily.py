from common.config import settings
from common.logger import logger
from tavily import TavilyClient


def web_search(query: str) -> str:
    """
    Search the web for information using Tavily. Use this tool to find current trends, news, and information about topics for content strategy creation.
    """

    client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    logger.info(f"Searching the web for information about: {query}")
    response = client.search(
        query=query,
        include_answer="basic",
        topic="news",
        search_depth="basic",
        max_results=3,
    )

    results = response.get("results", [])

    if not results:
        return "No results found for the search query."

    formatted_results = []
    for i, result in enumerate(results, 1):
        title = result.get("title", "No title")
        content = result.get("content", "")
        url = result.get("url", "")
        formatted_results.append(f"{i}. {title}\n{content}\nSource: {url}")

    logger.info(f"Returning {len(results)} search results")
    return "\n\n".join(formatted_results)

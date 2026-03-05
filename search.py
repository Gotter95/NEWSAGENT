"""Tavily web search wrapper."""

from tavily import TavilyClient
from config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)


def search_articles(query: str, max_results: int = 5) -> list[dict]:
    """Search for recent news articles using Tavily."""
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        topic="news",
    )
    return response.get("results", [])

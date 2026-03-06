"""Tavily web search wrapper."""

from tavily import TavilyClient
from config import TAVILY_API_KEY

client = TavilyClient(api_key=TAVILY_API_KEY)

VIDEO_PATTERNS = ["youtube.com/watch", "youtu.be/", "vimeo.com/"]


def _detect_content_type(url: str) -> str:
    """Detect if a URL points to a video or article."""
    return "video" if any(p in url for p in VIDEO_PATTERNS) else "article"


def search_articles(query: str, max_results: int = 5) -> list[dict]:
    """Search for recent news articles using Tavily with full content."""
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        topic="news",
        include_raw_content="markdown",
    )
    results = response.get("results", [])
    for r in results:
        r["content_type"] = _detect_content_type(r.get("url", ""))
        raw = r.get("raw_content") or r.get("content", "")
        r["full_content"] = raw[:4000]
    return results

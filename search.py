"""
Web search module using Tavily API.
Fetches recent news articles for a given client's industry.
"""

import httpx

from config import ClientConfig, TAVILY_API_KEY, MAX_RESULTS_PER_QUERY, get_date_range


async def search_news(client: ClientConfig) -> list[dict]:
    """
    Run multiple search queries for a client and return deduplicated results.
    Each result dict has: title, url, content, published_date, source
    """
    start_date, end_date = get_date_range()
    all_results = []
    seen_urls = set()

    queries = _build_queries(client)

    async with httpx.AsyncClient(timeout=30) as http:
        for query in queries:
            results = await _tavily_search(http, query, start_date, end_date)
            for r in results:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)

    return all_results


def _build_queries(client: ClientConfig) -> list[str]:
    """
    Build a set of search queries from the client config.
    Combines industry context with specific keywords and entities.
    """
    queries = []

    # Broad industry query
    queries.append(f"{client.industry} news this week")

    # Keyword-based queries (group 2-3 keywords per query for breadth)
    for i in range(0, len(client.keywords), 2):
        chunk = client.keywords[i : i + 2]
        queries.append(" ".join(chunk) + " news")

    # Entity-specific queries
    for entity in client.entities:
        queries.append(f"{entity} latest news")

    # Cross-cutting disruption queries: entity + industry (catches tech leaders
    # talking about this client's industry, e.g. "Dario Amodei consulting")
    for entity in client.entities:
        queries.append(f"{entity} {client.industry}")

    # Source-specific queries for preferred outlets
    if client.preferred_sources:
        source_sites = " OR ".join(
            f"site:{s}" for s in client.preferred_sources[:5]
        )
        queries.append(f"{client.industry} AI ({source_sites})")

    # Video-focused queries to surface interviews, talks, and clips
    queries.append(f"{client.industry} interview video this week")
    for entity in client.entities[:5]:
        queries.append(f"{entity} interview OR podcast OR video OR talk")

    return queries


async def _tavily_search(
    http: httpx.AsyncClient,
    query: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """Call Tavily search API and return normalized results."""
    try:
        resp = await http.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": MAX_RESULTS_PER_QUERY,
                "topic": "news",
                "days": 7,
                "include_answer": False,
                "include_raw_content": True,
            },
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [warn] Search failed for query '{query}': {e}")
        return []

    results = []
    for item in data.get("results", []):
        # Use raw_content for better date extraction, truncate to avoid
        # blowing up the Claude prompt (first 3000 chars is enough)
        raw = item.get("raw_content") or ""
        raw_snippet = raw[:3000] if raw else ""

        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "raw_content_snippet": raw_snippet,
                "published_date": item.get("published_date", ""),
                "source": _extract_domain(item.get("url", "")),
            }
        )

    return results


def _extract_domain(url: str) -> str:
    """Extract domain name from URL for display."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return url

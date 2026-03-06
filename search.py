"""
Web search module using Tavily API.
Fetches recent news articles for a given client's industry.

Search strategy: SIGNAL-FIRST
- Priority 1: Tech leaders / prominent people saying things about the client's industry
- Priority 2: Major disruptions, shifts, or data points in the industry
- Priority 3: General industry news (limited)
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
    Build search queries with SIGNAL-FIRST priority.
    Most queries target prominent people talking about the industry,
    not the industry talking about itself.
    """
    queries = []

    # --- TIER 1: Signal queries (tech leaders + industry) ---
    # These are the most valuable: prominent people commenting on this industry
    for entity in client.entities:
        # Direct: "Dario Amodei consulting" / "Sam Altman knowledge workers"
        queries.append(f'"{entity}" {client.industry}')
        # Quote-style: catch interviews, blog posts, keynotes
        queries.append(f'"{entity}" AI replacing {client.industry}')

    # Broader signal queries
    queries.append(f"CEO says AI will replace {client.industry}")
    queries.append(f"tech leader {client.industry} disruption AI")
    queries.append(f"AI automation threat {client.industry} future")

    # --- TIER 2: High-value keyword queries ---
    # Only use the most signal-rich keywords, not generic ones
    for kw in client.keywords:
        queries.append(f"{kw} 2026")

    # --- TIER 3: Interview/podcast sources (where leaders actually talk) ---
    for entity in client.entities[:5]:
        queries.append(f'"{entity}" interview podcast 2026')

    # --- TIER 4: Minimal broad industry (just 1-2 queries) ---
    queries.append(f"{client.industry} AI disruption news this week")

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

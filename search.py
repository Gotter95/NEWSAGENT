"""
Web search module using Tavily API.
Fetches recent news articles for a given client's industry.

Search strategy: SIGNAL-FIRST, QUOTA-EFFICIENT
- Keep total queries under 15 per client to stay within Tavily limits
- Combine entities into OR-style queries instead of one query per entity
- Prioritize signal queries (tech leaders + industry) over generic news
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
    print(f"  Running {len(queries)} search queries...")

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
    Build a focused set of search queries (target: 8-12 per client).
    Combines multiple entities/keywords into single queries to save API calls.
    """
    queries = []

    # Split entities into "people" (signal sources) vs "companies"
    # Heuristic: if it has a space and no "&" or "Group", it's probably a person
    people = []
    companies = []
    for e in client.entities:
        if any(word in e for word in ["&", "Group", "Consulting", "AI", "Hub"]):
            companies.append(e)
        elif " " in e:
            people.append(e)
        else:
            companies.append(e)

    # --- SIGNAL QUERIES (most important) ---
    # Batch people into groups of 3 for OR-style queries
    for i in range(0, len(people), 3):
        batch = people[i : i + 3]
        names = " OR ".join(batch)
        queries.append(f"({names}) {client.industry} AI")

    # One query for people + interviews/podcasts
    if people:
        top_people = " OR ".join(people[:4])
        queries.append(f"({top_people}) interview podcast AI")

    # --- INDUSTRY DISRUPTION QUERIES ---
    queries.append(f"AI replacing {client.industry} 2026")
    queries.append(f"AI disruption {client.industry} news")

    # --- COMPANY QUERIES (batch them) ---
    if companies:
        company_names = " OR ".join(companies[:5])
        queries.append(f"({company_names}) AI news 2026")

    # --- KEYWORD QUERIES (batch 3-4 per query) ---
    for i in range(0, len(client.keywords), 4):
        chunk = client.keywords[i : i + 4]
        queries.append(" OR ".join(chunk))

    # --- ONE BROAD QUERY ---
    queries.append(f"{client.industry} news this week")

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
        if resp.status_code == 432:
            print(f"  [warn] Rate limited (432) for query: {query[:60]}...")
            return []
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [warn] Search failed for query '{query[:60]}...': {e}")
        return []

    results = []
    for item in data.get("results", []):
        url = item.get("url", "")

        # Skip non-article URLs (homepages, category pages, etc.)
        if not _is_article_url(url):
            continue

        raw = item.get("raw_content") or ""
        raw_snippet = raw[:3000] if raw else ""

        results.append(
            {
                "title": item.get("title", ""),
                "url": url,
                "content": item.get("content", ""),
                "raw_content_snippet": raw_snippet,
                "published_date": item.get("published_date", ""),
                "source": _extract_domain(url),
            }
        )

    return results


def _is_article_url(url: str) -> bool:
    """
    Filter out URLs that are likely homepages or category pages, not individual articles.
    An article URL typically has a path with multiple segments, a slug, or date components.
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")

        # Reject bare homepages: e.g. https://example.com or https://example.com/
        if not path or path == "":
            return False

        # Reject shallow category pages: /news, /blog, /articles, /topics
        segments = [s for s in path.split("/") if s]
        if len(segments) == 1 and segments[0] in (
            "news", "blog", "articles", "topics", "insights", "research",
            "about", "contact", "careers", "podcasts", "events",
        ):
            return False

        # Accept anything with 2+ path segments (likely an article)
        # e.g. /2026/03/article-slug or /news/article-title
        return True
    except Exception:
        return True  # If we can't parse, let it through


def _extract_domain(url: str) -> str:
    """Extract domain name from URL for display."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return url

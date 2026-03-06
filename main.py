"""NEWSAGENT — AI-powered newsletter research agent."""

from config import CLIENTS
from search import search_articles
from analyze import analyze_articles
from notion_client import publish_to_notion


def run():
    """Run the newsletter pipeline for all clients."""
    for client_name, info in CLIENTS.items():
        print(f"\n{'='*60}")
        print(f"Processing: {client_name}")
        print(f"{'='*60}")

        # 1. Search (deduplicate by URL)
        all_articles = []
        seen_urls = set()
        for query in info["queries"]:
            print(f"  Searching: {query}")
            results = search_articles(query)
            for r in results:
                url = r.get("url")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_articles.append(r)
        print(f"  Found {len(all_articles)} unique articles total")

        # 2. Analyze
        print("  Analyzing with Claude...")
        brief = analyze_articles(all_articles, client_name, info["industry"])
        print(f"  Brief generated ({len(brief)} chars)")

        # 3. Publish
        try:
            print("  Publishing to Notion...")
            url = publish_to_notion(client_name, brief)
            print(f"  Published: {url}")
        except Exception as e:
            print(f"  ERROR publishing {client_name}: {e}")

    print("\nDone!")


if __name__ == "__main__":
    run()

"""
Weekly News Intelligence Agent
Searches for industry news, analyzes with Claude, and pushes to Notion.

Usage:
    python main.py                    # Run for all clients
    python main.py --client "Name"    # Run for a specific client
    python main.py --dry-run          # Search + analyze but skip Notion
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime

from config import CLIENTS, TAVILY_API_KEY, ANTHROPIC_API_KEY, NOTION_API_KEY, NOTION_PARENT_PAGE_ID
from search import search_news
from analyze import analyze_news
from notion_client import create_weekly_page


def check_config():
    """Validate that required API keys are set."""
    missing = []
    if not TAVILY_API_KEY:
        missing.append("TAVILY_API_KEY")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not NOTION_API_KEY:
        missing.append("NOTION_API_KEY")
    if not NOTION_PARENT_PAGE_ID:
        missing.append("NOTION_PARENT_PAGE_ID")

    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("Set them before running:")
        for var in missing:
            print(f"  export {var}=your_key_here")
        sys.exit(1)


async def run_for_client(client_config, dry_run=False):
    """Run the full pipeline for a single client."""
    print(f"\n{'='*60}")
    print(f"  {client_config.name} — {client_config.industry}")
    print(f"  Week of {datetime.now().strftime('%B %d, %Y')}")
    print(f"{'='*60}")

    # Step 1: Search
    print("\n[1/3] Searching for news...")
    articles = await search_news(client_config)
    print(f"  Found {len(articles)} unique articles")

    if not articles:
        print("  No articles found. Skipping analysis.")
        return

    # Step 2: Analyze with Claude
    print("\n[2/3] Analyzing with Claude...")
    briefing = await analyze_news(articles, client_config)

    analyzed_count = len(briefing.get("articles", []))
    themes = briefing.get("trending_themes", [])
    opportunities = len(briefing.get("content_opportunities", []))

    print(f"  Kept {analyzed_count} relevant articles")
    print(f"  Themes: {', '.join(themes)}")
    print(f"  Content opportunities: {opportunities}")

    if dry_run:
        print("\n[DRY RUN] Skipping Notion. Here's the briefing:\n")
        print(json.dumps(briefing, indent=2, default=str))
        return

    # Step 3: Push to Notion
    print("\n[3/3] Creating Notion page...")
    page_url = await create_weekly_page(briefing, client_config.name)
    print(f"\n  Done! View your briefing: {page_url}")


async def main():
    parser = argparse.ArgumentParser(description="Weekly News Intelligence Agent")
    parser.add_argument(
        "--client",
        type=str,
        help="Run for a specific client by name (default: all clients)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search and analyze but don't push to Notion",
    )
    args = parser.parse_args()

    if not args.dry_run:
        check_config()
    else:
        # For dry run, only need Tavily + Anthropic
        missing = []
        if not TAVILY_API_KEY:
            missing.append("TAVILY_API_KEY")
        if not ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if missing:
            print(f"Error: Missing environment variables: {', '.join(missing)}")
            sys.exit(1)

    # Filter clients if specified
    clients = CLIENTS
    if args.client:
        clients = [c for c in CLIENTS if c.name.lower() == args.client.lower()]
        if not clients:
            print(f"Error: No client found with name '{args.client}'")
            print(f"Available clients: {', '.join(c.name for c in CLIENTS)}")
            sys.exit(1)

    print(f"Running weekly news agent for {len(clients)} client(s)...")

    for client_config in clients:
        await run_for_client(client_config, dry_run=args.dry_run)

    print("\n\nAll done!")


if __name__ == "__main__":
    asyncio.run(main())

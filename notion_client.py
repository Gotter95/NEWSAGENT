"""
Notion integration module.
Creates a weekly briefing page in Notion with structured content.
"""

from datetime import datetime

import httpx

from config import NOTION_API_KEY, NOTION_PARENT_PAGE_ID

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


async def create_weekly_page(briefing: dict, client_name: str) -> str:
    """
    Create a Notion page with the weekly briefing content.
    Returns the URL of the created page.
    """
    week_of = datetime.now().strftime("%B %d, %Y")
    title = f"Weekly Intel — {client_name} — {week_of}"

    # Build the page content blocks
    children = _build_blocks(briefing)

    payload = {
        "parent": {"page_id": NOTION_PARENT_PAGE_ID},
        "properties": {
            "title": [{"text": {"content": title}}],
        },
        "children": children,
    }

    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            f"{NOTION_API_URL}/pages",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    page_url = data.get("url", "")
    page_id = data.get("id", "")
    print(f"  Created Notion page: {page_url}")

    # Notion limits children to 100 blocks per request.
    # If we have overflow, append in batches.
    if len(children) > 100:
        overflow = children[100:]
        for i in range(0, len(overflow), 100):
            batch = overflow[i : i + 100]
            async with httpx.AsyncClient(timeout=30) as http:
                await http.patch(
                    f"{NOTION_API_URL}/blocks/{page_id}/children",
                    headers=_headers(),
                    json={"children": batch},
                )

    return page_url


def _build_blocks(briefing: dict) -> list[dict]:
    """Convert the briefing JSON into Notion block objects."""
    blocks = []

    # --- Top Articles ---
    articles = briefing.get("articles", [])
    if articles:
        # Sort by relevance score descending
        articles.sort(key=lambda a: a.get("relevance_score", 0), reverse=True)

        blocks.append(_heading1("Top Articles This Week"))

        for i, article in enumerate(articles, 1):
            title = article.get("title", "Untitled")
            source = article.get("source", "")
            url = article.get("url", "")
            date = article.get("date", "")
            summary = article.get("summary", "")
            score = article.get("relevance_score", "?")
            quotes = article.get("key_quotes", [])
            angles = article.get("content_angles", [])

            # Article heading with link
            has_video = article.get("has_video", False)
            video_tag = " [VIDEO]" if has_video else ""
            blocks.append(_heading2(f"{i}. {title}{video_tag}"))

            # Metadata line
            meta = f"Source: {source} | Date: {date} | Relevance: {score}/10"
            blocks.append(_paragraph(meta))

            # Link
            if url:
                blocks.append(_bookmark(url))

            # Summary
            blocks.append(_paragraph(summary))

            # Key quotes
            if quotes:
                blocks.append(_heading3("Key Quotes"))
                for quote in quotes:
                    blocks.append(_quote(quote))

            # Content angles
            if angles:
                blocks.append(_heading3("Content Angles"))
                for angle in angles:
                    blocks.append(_bulleted_list_item(angle))

            blocks.append(_divider())

    # --- Content Opportunities ---
    opportunities = briefing.get("content_opportunities", [])
    if opportunities:
        blocks.append(_heading1("Content Opportunities"))

        for opp in opportunities:
            idea = opp.get("idea", "")
            fmt = opp.get("format", "")
            angle = opp.get("angle", "")

            blocks.append(_heading3(f"{idea} [{fmt}]"))
            blocks.append(_paragraph(angle))

            source_articles = opp.get("source_articles", [])
            if source_articles:
                for sa in source_articles:
                    blocks.append(_bulleted_list_item(sa))

    return blocks


# --- Notion block helpers ---

def _heading1(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_1",
        "heading_1": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _heading2(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _heading3(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _paragraph(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _bulleted_list_item(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _quote(text: str) -> dict:
    return {
        "object": "block",
        "type": "quote",
        "quote": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _bookmark(url: str) -> dict:
    return {
        "object": "block",
        "type": "bookmark",
        "bookmark": {"url": url},
    }

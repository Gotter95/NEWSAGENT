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
        "children": children[:100],
    }

    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.post(
            f"{NOTION_API_URL}/pages",
            headers=_headers(),
            json=payload,
        )
        if resp.status_code >= 400:
            print(f"  [error] Notion API returned {resp.status_code}: {resp.text[:500]}")
        resp.raise_for_status()
        data = resp.json()

    page_url = data.get("url", "")
    page_id = data.get("id", "")
    print(f"  Created Notion page: {page_url}")

    # Notion limits children to 100 blocks per request.
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

    # --- SIGNALS ---
    signals = briefing.get("signals", [])
    if signals:
        blocks.append(_heading1("SIGNALS — What prominent people said this week"))
        blocks.append(_callout(
            "These are high-priority. A tech leader or major figure said something "
            "relevant to your industry. React to these first."
        ))

        for signal in signals:
            headline = signal.get("headline", "")
            who = signal.get("who", "")
            what = signal.get("what_they_said", "")
            url = signal.get("source_url", "")
            source = signal.get("source_name", "")
            date = signal.get("date", "")
            why = signal.get("why_this_matters", "")
            play = signal.get("the_play", "")

            blocks.append(_heading2(headline))
            blocks.append(_paragraph(f"{who} — {source}, {date}"))

            if url:
                blocks.append(_bookmark(url))

            if what:
                blocks.append(_quote(what))

            if why:
                blocks.append(_paragraph(f"Why it matters: {why}"))

            if play:
                blocks.append(_heading3("THE PLAY"))
                blocks.append(_callout(play))

            blocks.append(_divider())

    # --- STORIES ---
    stories = briefing.get("stories", [])
    if stories:
        blocks.append(_heading1("STORIES — News worth posting about"))

        for story in stories:
            headline = story.get("headline", "")
            url = story.get("source_url", "")
            source = story.get("source_name", "")
            date = story.get("date", "")
            one_line = story.get("one_line", "")
            stat = story.get("key_stat_or_quote", "")
            play = story.get("the_play", "")

            blocks.append(_heading2(headline))
            blocks.append(_paragraph(f"{source}, {date}"))

            if url:
                blocks.append(_bookmark(url))

            if one_line:
                blocks.append(_paragraph(one_line))

            if stat:
                blocks.append(_quote(stat))

            if play:
                blocks.append(_heading3("THE PLAY"))
                blocks.append(_callout(play))

            blocks.append(_divider())

    # --- POST IDEAS ---
    post_ideas = briefing.get("post_ideas", [])
    if post_ideas:
        blocks.append(_heading1("READY-TO-GO POST IDEAS"))

        for i, idea in enumerate(post_ideas, 1):
            hook = idea.get("hook", "")
            angle = idea.get("angle", "")
            fmt = idea.get("format", "text")

            blocks.append(_heading3(f"Idea {i} [{fmt.upper()}]"))
            if hook:
                blocks.append(_callout(f"Hook: {hook}"))
            if angle:
                blocks.append(_paragraph(f"Angle: {angle}"))

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


def _callout(text: str) -> dict:
    return {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}],
            "icon": {"type": "emoji", "emoji": "💡"},
        },
    }


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _bookmark(url: str) -> dict:
    return {
        "object": "block",
        "type": "bookmark",
        "bookmark": {"url": url},
    }

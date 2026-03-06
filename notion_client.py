"""Publish newsletter briefs to Notion."""

import httpx
from datetime import date
from config import NOTION_API_KEY, NOTION_PARENT_PAGE_ID

NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}


def _text_block(block_type: str, text: str) -> dict:
    """Create a Notion block with rich_text content."""
    return {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": _parse_rich_text(text[:2000])
        },
    }


import re

def _parse_rich_text(text: str) -> list[dict]:
    """Parse markdown-style [text](url) links into Notion rich_text segments."""
    parts = []
    last_end = 0
    for m in re.finditer(r'\[([^\]]+)\]\((https?://[^\)]+)\)', text):
        # Plain text before the link
        if m.start() > last_end:
            parts.append({
                "type": "text",
                "text": {"content": text[last_end:m.start()]}
            })
        # The link itself
        parts.append({
            "type": "text",
            "text": {"content": m.group(1), "link": {"url": m.group(2)}}
        })
        last_end = m.end()
    # Remaining text after the last link
    if last_end < len(text):
        parts.append({
            "type": "text",
            "text": {"content": text[last_end:]}
        })
    return parts if parts else [{"type": "text", "text": {"content": text}}]


def _build_rich_blocks(brief: dict) -> list[dict]:
    """Convert a structured brief dict into Notion API blocks."""
    blocks = []

    # Headline
    if headline := brief.get("headline"):
        blocks.append(_text_block("heading_1", headline))

    # Intro
    if intro := brief.get("intro"):
        blocks.append(_text_block("paragraph", intro))

    # Sections
    for i, section in enumerate(brief.get("sections", [])):
        if i > 0:
            blocks.append({"object": "block", "type": "divider", "divider": {}})

        # Section heading
        blocks.append(_text_block("heading_2", section.get("heading", "")))

        # Body
        if body := section.get("body"):
            blocks.append(_text_block("paragraph", body))

        # Why it matters — callout block
        if why := section.get("why_it_matters"):
            blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": why[:2000]}}],
                    "icon": {"type": "emoji", "emoji": "\U0001f4a1"},
                },
            })

        # Source links
        for source in section.get("sources", []):
            url = source.get("url", "")
            source_type = source.get("type", "article")

            if source_type == "video" and "youtube.com" in url:
                blocks.append({
                    "object": "block",
                    "type": "video",
                    "video": {"type": "external", "external": {"url": url}},
                })
            elif source_type == "video":
                blocks.append({
                    "object": "block",
                    "type": "embed",
                    "embed": {"url": url},
                })
            elif url:
                blocks.append({
                    "object": "block",
                    "type": "bookmark",
                    "bookmark": {"url": url},
                })

    # Video links section
    video_links = brief.get("video_links", [])
    if video_links:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append(_text_block("heading_2", "Videos & Media"))
        for vid in video_links:
            vid_url = vid.get("url", "")
            if vid_url:
                # Add title as text
                if vid_title := vid.get("title"):
                    blocks.append(_text_block("paragraph", f"▶ {vid_title}"))
                # Embed the video
                if "youtube.com" in vid_url or "youtu.be" in vid_url:
                    blocks.append({
                        "object": "block",
                        "type": "video",
                        "video": {"type": "external", "external": {"url": vid_url}},
                    })
                else:
                    blocks.append({
                        "object": "block",
                        "type": "embed",
                        "embed": {"url": vid_url},
                    })

    # Action items
    action_items = brief.get("action_items", [])
    if action_items:
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append(_text_block("heading_2", "Action Items"))
        for item in action_items:
            blocks.append(_text_block("bulleted_list_item", item))

    # Notion API limit: 100 blocks per request
    return blocks[:100]


def _build_plain_blocks(brief: str) -> list[dict]:
    """Fallback: split plain text into paragraph chunks."""
    chunks = [brief[i : i + 2000] for i in range(0, len(brief), 2000)]
    return [_text_block("paragraph", chunk) for chunk in chunks]


def publish_to_notion(client_name: str, brief: dict | str) -> str:
    """Create a new Notion page with the newsletter brief."""
    today = date.today().isoformat()

    if isinstance(brief, dict):
        children = _build_rich_blocks(brief)
    else:
        children = _build_plain_blocks(brief)

    payload = {
        "parent": {"page_id": NOTION_PARENT_PAGE_ID},
        "properties": {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": f"{client_name} — Newsletter Brief {today}"
                        }
                    }
                ]
            }
        },
        "children": children,
    }

    resp = httpx.post(
        "https://api.notion.com/v1/pages", headers=HEADERS, json=payload
    )
    if resp.status_code != 200:
        print(f"  Notion API error {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    return resp.json().get("url", "Published (no URL returned)")

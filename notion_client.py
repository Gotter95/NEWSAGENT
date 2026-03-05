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


def publish_to_notion(client_name: str, brief: str) -> str:
    """Create a new Notion page with the newsletter brief."""
    today = date.today().isoformat()

    # Split brief into blocks (Notion has a 2000-char limit per block)
    chunks = [brief[i : i + 2000] for i in range(0, len(brief), 2000)]

    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}]
            },
        }
        for chunk in chunks
    ]

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
    )    if resp.status_code != 200:
        print(f"  Notion API error {resp.status_code}: {resp.text}")

    resp.raise_for_status()
    return resp.json().get("url", "Published (no URL returned)")

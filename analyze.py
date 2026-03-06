"""Analyze articles with Claude and produce a newsletter brief."""

import json
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def analyze_articles(articles: list[dict], client_name: str, industry: str) -> dict | str:
    """Use Claude to summarize articles into a structured newsletter brief.

    Returns a dict (structured JSON) on success, or a raw string as fallback.
    """
    if not articles:
        return f"No articles found for {client_name}."

    articles_text = ""
    for i, art in enumerate(articles, 1):
        articles_text += (
            f"\n---\nArticle {i}\n"
            f"Title: {art.get('title', 'N/A')}\n"
            f"URL: {art.get('url', 'N/A')}\n"
            f"Type: {art.get('content_type', 'article')}\n"
            f"Content: {art.get('full_content', art.get('content', 'N/A'))}\n"
        )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are a newsletter curator for {client_name} "
                    f"(industry: {industry}).\n\n"
                    f"Analyze these articles and produce a newsletter brief.\n\n"
                    f"You MUST respond with valid JSON only (no markdown fences, no extra text). "
                    f"Use this exact structure:\n"
                    f'{{\n'
                    f'  "headline": "A catchy newsletter headline",\n'
                    f'  "sections": [\n'
                    f'    {{\n'
                    f'      "heading": "Insight title",\n'
                    f'      "body": "2-3 sentence explanation of this insight.",\n'
                    f'      "why_it_matters": "Why this matters for {client_name}.",\n'
                    f'      "sources": [\n'
                    f'        {{"title": "Article title", "url": "https://...", "type": "article"}}\n'
                    f'      ]\n'
                    f'    }}\n'
                    f'  ],\n'
                    f'  "action_items": ["Action item 1", "Action item 2"]\n'
                    f'}}\n\n'
                    f"Include 3-5 sections. For each source, set type to \"video\" if "
                    f"the URL is a YouTube or Vimeo link, otherwise \"article\".\n"
                    f"Include the actual source URLs from the articles.\n\n"
                    f"Articles:\n{articles_text}"
                ),
            }
        ],
    )

    raw_text = message.content[0].text
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"  Warning: Claude did not return valid JSON, using raw text fallback")
        return raw_text

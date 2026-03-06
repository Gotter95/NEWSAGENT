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
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are a newsletter curator for {client_name} "
                    f"(industry: {industry}).\n\n"
                    f"Group these articles by topic and produce a structured brief.\n\n"
                    f"You MUST respond with valid JSON only (no markdown fences, no extra text). "
                    f"Use this exact structure:\n"
                    f'{{\n'
                    f'  "headline": "A catchy newsletter headline",\n'
                    f'  "intro": "A 2-3 sentence overview of this edition.",\n'
                    f'  "sections": [\n'
                    f'    {{\n'
                    f'      "heading": "Topic title",\n'
                    f'      "summary": "2-3 sentence summary of this topic.",\n'
                    f'      "articles": [\n'
                    f'        {{\n'
                    f'          "title": "Exact article title",\n'
                    f'          "url": "https://exact-url-from-source",\n'
                    f'          "type": "article",\n'
                    f'          "excerpt": "A 3-5 sentence excerpt of the most important/interesting content from this article. Pull actual facts, data, quotes, and key points directly from the article content."\n'
                    f'        }}\n'
                    f'      ]\n'
                    f'    }}\n'
                    f'  ],\n'
                    f'  "action_items": ["Specific action item 1", "Specific action item 2"]\n'
                    f'}}\n\n'
                    f"IMPORTANT RULES:\n"
                    f"- Group related articles together under topic sections (3-5 sections).\n"
                    f"- EVERY article must appear in exactly one section.\n"
                    f"- For each article, the excerpt MUST contain real content pulled from the article — key facts, data, quotes, insights. NOT a generic summary.\n"
                    f"- Use the EXACT title and URL from each article. Do NOT make up URLs.\n"
                    f"- Set type to \"video\" if the URL contains youtube.com, youtu.be, or vimeo.com. Otherwise \"article\".\n"
                    f"- The summary is just a brief 2-3 sentence topic intro. The articles and excerpts are the main content.\n\n"
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

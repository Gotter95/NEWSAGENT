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
                    f"Analyze these articles and produce a DETAILED newsletter brief.\n\n"
                    f"You MUST respond with valid JSON only (no markdown fences, no extra text). "
                    f"Use this exact structure:\n"
                    f'{{\n'
                    f'  "headline": "A catchy newsletter headline",\n'
                    f'  "intro": "A 2-3 sentence overview of this edition.",\n'
                    f'  "sections": [\n'
                    f'    {{\n'
                    f'      "heading": "Insight title",\n'
                    f'      "body": "A DETAILED 5-8 sentence deep-dive into this insight. Reference specific data, quotes, and facts from the articles. Mention the source by name inline (e.g. According to [Source Title](url)...).",\n'
                    f'      "why_it_matters": "3-4 sentences on why this matters for {client_name} and what they should do about it.",\n'
                    f'      "sources": [\n'
                    f'        {{"title": "Article title", "url": "https://...", "type": "article"}}\n'
                    f'      ]\n'
                    f'    }}\n'
                    f'  ],\n'
                    f'  "video_links": [\n'
                    f'    {{"title": "Video title", "url": "https://youtube.com/..."}}\n'
                    f'  ],\n'
                    f'  "action_items": ["Specific action item 1", "Specific action item 2"]\n'
                    f'}}\n\n'
                    f"IMPORTANT RULES:\n"
                    f"- Include 4-6 sections with LONG, DETAILED body text (5-8 sentences each).\n"
                    f"- In the body, reference sources by name and include their URLs inline using markdown link syntax.\n"
                    f"- Every source MUST include the real URL from the articles provided.\n"
                    f"- For each source, set type to \"video\" if the URL is YouTube or Vimeo, otherwise \"article\".\n"
                    f"- Collect ALL YouTube/Vimeo video URLs from the articles into the video_links array.\n"
                    f"- Action items should be specific and actionable, not generic.\n"
                    f"- Write in a professional but engaging tone.\n\n"
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

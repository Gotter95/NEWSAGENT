"""Analyze articles with Claude and produce a newsletter brief."""

import json
import anthropic
from config import ANTHROPIC_API_KEY

api_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = (
    "You are a JSON API that produces newsletter briefs. "
    "You ONLY output valid JSON. No markdown, no commentary, no extra text. "
    "Your entire response must be a single JSON object."
)

MAX_RETRIES = 2


def _build_user_prompt(articles_text: str, client_name: str, industry: str) -> str:
    return (
        f"You are a newsletter curator for {client_name} "
        f"(industry: {industry}).\n\n"
        f"Group these articles by topic and produce a structured brief.\n\n"
        f"Respond with ONLY a JSON object using this exact structure:\n"
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
        f'- Set type to "video" if the URL contains youtube.com, youtu.be, or vimeo.com. Otherwise "article".\n'
        f"- The summary is just a brief 2-3 sentence topic intro. The articles and excerpts are the main content.\n\n"
        f"Articles:\n{articles_text}"
    )


def _call_claude(articles_text: str, client_name: str, industry: str) -> dict:
    """Call Claude with prefill to force JSON output. Retries on parse failure."""
    user_prompt = _build_user_prompt(articles_text, client_name, industry)

    for attempt in range(1, MAX_RETRIES + 1):
        message = api_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": "{"},
            ],
        )

        raw_text = "{" + message.content[0].text
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            print(f"  Warning: JSON parse failed (attempt {attempt}/{MAX_RETRIES})")
            # Try to extract JSON from the response
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(raw_text[start:end])
                except json.JSONDecodeError:
                    pass

    print("  ERROR: All JSON parse attempts failed, returning raw text")
    return raw_text


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

    return _call_claude(articles_text, client_name, industry)

"""Analyze articles with Claude and produce a newsletter brief."""

import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def analyze_articles(articles: list[dict], client_name: str, industry: str) -> str:
    """Use Claude to summarize articles into a newsletter brief."""
    if not articles:
        return f"No articles found for {client_name}."

    articles_text = ""
    for i, art in enumerate(articles, 1):
        articles_text += (
            f"\n---\nArticle {i}\n"
            f"Title: {art.get('title', 'N/A')}\n"
            f"URL: {art.get('url', 'N/A')}\n"
            f"Content: {art.get('content', 'N/A')[:1000]}\n"
        )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": (
                    f"You are a newsletter curator for {client_name} "
                    f"(industry: {industry}).\n\n"
                    f"Analyze these articles and produce a concise newsletter "
                    f"brief with:\n"
                    f"1. A catchy headline\n"
                    f"2. 3-5 key insights (2-3 sentences each)\n"
                    f"3. Why each insight matters for {client_name}\n"
                    f"4. Suggested action items\n\n"
                    f"Articles:\n{articles_text}"
                ),
            }
        ],
    )
    return message.content[0].text

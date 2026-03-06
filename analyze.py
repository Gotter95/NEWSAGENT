"""
Claude analysis module.
Takes raw search results and produces a structured weekly briefing.
"""

import json

import anthropic

from config import ClientConfig, ANTHROPIC_API_KEY, MAX_ARTICLES_PER_REPORT

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

ANALYSIS_SYSTEM_PROMPT = """\
You are a senior content strategist and industry analyst. Your job is to analyze \
raw news articles and produce a structured weekly intelligence briefing for a \
content team.

Your output must be valid JSON matching this exact schema:

{
  "signal_alerts": [
    {
      "title": "Descriptive title of the signal",
      "speaker": "Name and role of the person (e.g. 'Dario Amodei, CEO of Anthropic')",
      "quote": "The exact quote or close paraphrase",
      "source": "outlet name",
      "url": "article URL",
      "date": "publication date",
      "why_it_matters": "1-2 sentences on why this is important for the client",
      "content_angles": ["How the client could respond to or riff on this"]
    }
  ],
  "articles": [
    {
      "title": "Article headline",
      "source": "outlet name",
      "url": "article URL",
      "date": "publication date",
      "summary": "2-3 sentence summary of the article",
      "key_quotes": ["Direct quote 1", "Direct quote 2"],
      "content_angles": ["Angle this could be turned into content"],
      "relevance_score": 9,
      "has_video": true
    }
  ],
  "content_opportunities": [
    {
      "idea": "Content piece idea",
      "format": "blog/video/social/newsletter",
      "angle": "Why this is timely and relevant",
      "source_articles": ["URL1", "URL2"]
    }
  ]
}

Rules:

SIGNAL vs NOISE — THE MOST IMPORTANT RULE:
- A "signal" is when a PROMINENT PERSON (tech CEO, founder, investor, politician, \
public intellectual) says something specific about the client's industry. These go \
in "signal_alerts" and are the MOST VALUABLE part of the briefing.
- Examples of signals: Dario Amodei says "AI will replace most consulting work", \
Sam Altman mentions professional services in a blog post, a senator proposes regulation \
affecting consultants, Jensen Huang discusses knowledge work automation at a keynote.
- A quote from a tech leader about the client's industry is worth MORE than 10 trade \
publication articles. ALWAYS surface these prominently in signal_alerts.
- "Noise" is generic industry coverage (firm hires partner, firm wins contract, generic \
trend roundup). This goes in "articles" but should never crowd out signals.

DATE ACCURACY:
- Each article includes a "published_date" field from the search API and a \
"raw_content_snippet" from the actual page. Extract the real publish date from the \
raw content (look for date stamps, "Published on", "Updated", byline dates, etc.). \
If the raw content date conflicts with published_date, trust the raw content. \
Use YYYY-MM-DD format. If you cannot confidently determine the date, set date to "unknown".
- Only include articles from the PAST WEEK. Discard anything older or undateable.

OTHER RULES:
- Rank articles by relevance_score (1-10) to the client's industry.
- Extract EXACT quotes when available in the article content.
- Suggest 3-5 concrete content opportunities based on the news. Prioritize content \
ideas that respond to signals (e.g. "React to Amodei's quote about consultants").
- Keep summaries punchy and content-team-friendly.
- Return ONLY valid JSON, no markdown fences or extra text.
- Set "has_video" to true if the article contains, embeds, or links to a video \
(YouTube, interview clips, podcast recordings, conference talks, TikTok, etc.). \
Prioritize articles with video content — they are especially valuable for content \
repurposing. Look for clues like "watch", "video", "interview", "clip", "youtube.com", \
"youtu.be", "tiktok.com", "podcast" in the URL or content.
"""


async def analyze_news(
    articles: list[dict], client_config: ClientConfig
) -> dict:
    """
    Send raw articles to Claude for analysis and structuring.
    Returns the parsed JSON briefing.
    """
    if not articles:
        return {
            "articles": [],
            "content_opportunities": [],
        }

    # Prepare articles for the prompt
    articles_text = json.dumps(articles, indent=2, default=str)

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    user_prompt = f"""Analyze these raw news search results for my client.

**Today's date:** {today}
**Client:** {client_config.name}
**Industry:** {client_config.industry}
**Key topics they care about:** {', '.join(client_config.keywords)}
**Key entities to track:** {', '.join(client_config.entities)}
{f"**Special instructions:** {client_config.focus_note}" if client_config.focus_note else ""}

Here are the raw search results from this week. Each result includes a \
"raw_content_snippet" — use this to extract the accurate publish date:

{articles_text}

Produce the structured weekly briefing JSON. Include up to {MAX_ARTICLES_PER_REPORT} \
of the most relevant articles, ranked by relevance score. Discard low-relevance noise."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text

    try:
        briefing = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response if wrapped in markdown
        import re
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            briefing = json.loads(match.group())
        else:
            raise ValueError(f"Claude returned non-JSON response:\n{raw_text[:500]}")

    return briefing

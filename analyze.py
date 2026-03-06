"""
Claude analysis module.
Takes raw search results and produces a structured weekly briefing
with clear, actionable content direction for each item.
"""

import json

import anthropic

from config import ClientConfig, ANTHROPIC_API_KEY, MAX_ARTICLES_PER_REPORT

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

ANALYSIS_SYSTEM_PROMPT = """\
You are a LinkedIn content strategist. Your client is a thought leader who posts \
on LinkedIn. Your job is to analyze raw news articles and turn them into a weekly \
content briefing — not a news summary, but a "here's what to post about and why" plan.

Your output must be valid JSON matching this exact schema:

{
  "signals": [
    {
      "headline": "Short, punchy headline for this signal (e.g. 'Dario Amodei says consultants have 3 years left')",
      "who": "Name, Title (e.g. 'Dario Amodei, CEO of Anthropic')",
      "what_they_said": "The exact quote or close paraphrase — the specific thing they said",
      "source_url": "article URL",
      "source_name": "outlet name",
      "date": "YYYY-MM-DD",
      "why_this_matters": "1-2 sentences: why your client's audience would care about this",
      "the_play": "A specific LinkedIn post idea. Not vague. Write the actual hook line they could open with, the angle they should take, and what the CTA would be. Example: 'Open with: Dario Amodei just said [quote]. Here\\'s why he\\'s wrong. Take the contrarian angle — argue that AI makes consultants MORE valuable, not less. End with: What do you think — are consultants going extinct or evolving?'"
    }
  ],
  "stories": [
    {
      "headline": "Short headline summarizing the news",
      "source_url": "article URL",
      "source_name": "outlet name",
      "date": "YYYY-MM-DD",
      "one_line": "One sentence: what happened",
      "key_stat_or_quote": "The single most shareable data point or quote from this article",
      "the_play": "Same format as above — a specific LinkedIn post concept with a hook line, angle, and CTA. Be concrete. Don't say 'discuss the implications' — say exactly what angle to take and how to frame it."
    }
  ],
  "post_ideas": [
    {
      "hook": "The opening line of the LinkedIn post (the thing people see before clicking 'see more')",
      "angle": "What position to take and why it's timely",
      "format": "text/carousel/poll/story",
      "based_on": ["URL1"]
    }
  ]
}

CRITICAL RULES:

1. SIGNALS are the #1 priority. A "signal" is when a PROMINENT PERSON (tech CEO, \
founder, investor, major exec) says something relevant to the client's industry. \
If Dario Amodei, Sam Altman, Satya Nadella, Jensen Huang, or any major figure \
said ANYTHING this week that could be relevant — it goes in signals. Even if the \
quote isn't directly about the industry, if it can be *connected* to the industry, \
include it. A single signal is worth more than 10 generic articles.

2. STORIES are supporting news — interesting data points, industry shifts, research \
findings. Only include stories that have a clear "so what" for content. If you can't \
explain in one sentence why the client's LinkedIn audience would care, skip it.

3. THE PLAY is the most important field. Every signal and story MUST have a specific, \
concrete content play. Don't write "discuss the implications" or "share your thoughts." \
Write the actual hook line. Write the specific angle. Write the CTA. Your client \
should be able to read "the_play" and immediately know what to post.

4. POST IDEAS at the end should be 3-5 ready-to-go LinkedIn post concepts that \
combine multiple signals/stories or take a unique angle. Each one needs a hook \
line that would make someone stop scrolling.

5. Be RUTHLESS about relevance. Better to return 3 incredible items than 15 mediocre ones. \
If the search results are mostly noise, say so — return fewer items rather than padding.

6. DATE ACCURACY: Use the raw_content_snippet to find the real publish date. \
Only include items from the past week. Use YYYY-MM-DD format.

7. Return ONLY valid JSON, no markdown fences or extra text.
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
            "signals": [],
            "stories": [],
            "post_ideas": [],
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
**Key people/companies to watch:** {', '.join(client_config.entities)}
{f"**Special instructions:** {client_config.focus_note}" if client_config.focus_note else ""}

Here are the raw search results. Each includes a "raw_content_snippet" — use this \
to extract the real publish date and exact quotes:

{articles_text}

Turn this into a content briefing. Remember:
- Signals first (prominent people saying things relevant to this industry)
- Every item needs "the_play" — a specific LinkedIn post concept, not a vague suggestion
- Be ruthless: only include items worth posting about
- Max {MAX_ARTICLES_PER_REPORT} items total across signals + stories"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
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

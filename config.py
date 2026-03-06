"""
Configuration for the weekly news agent.
Define your clients and their industry keywords here.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ClientConfig:
    name: str
    industry: str
    keywords: list[str]
    # Key people/companies to track
    entities: list[str] = field(default_factory=list)
    # Specific outlets to prioritize (optional)
    preferred_sources: list[str] = field(default_factory=list)
    # Extra instructions for Claude when analyzing this client's news
    focus_note: str = ""


# --- Define your clients here ---
CLIENTS = [
    ClientConfig(
        name="Carla Cherry — Power Offer Consultants",
        industry="Management Consulting",
        keywords=[
            "consulting industry trends",
            "management consulting",
            "consultancies AI disruption",
            "AI replacing consultants",
            "AI agents replace knowledge workers",
            "AI tools for consulting",
            "consulting firm strategy",
            "boutique consulting growth",
            "consulting business development",
            "future of professional services AI",
            "AI strategy consulting threat",
            "autonomous AI agents consulting",
        ],
        entities=[
            # Consulting firms
            "McKinsey",
            "Bain & Company",
            "Boston Consulting Group",
            "Deloitte Consulting",
            "Accenture",
            # Tech leaders who comment on consulting/knowledge work disruption
            "Dario Amodei",
            "Sam Altman",
            "Satya Nadella",
            "Sundar Pichai",
            "Jensen Huang",
            "Marc Andreessen",
            "Marc Benioff",
        ],
        preferred_sources=[
            "consultancy.org",
            "hbr.org",
            "forbes.com",
            "businessinsider.com",
            "cnbc.com",
            "fortune.com",
            "ft.com",
            # Blogs and essay sources
            "darioamodei.com",
            "stratechery.com",
            "every.to",
            # Podcast/interview transcript sources
            "dwarkeshpatel.com",
            "lexfridman.com",
            "youtube.com",
        ],
        focus_note=(
            "CRITICAL: This client needs to know when prominent tech leaders (CEOs, "
            "founders, AI researchers) make statements about consulting, professional "
            "services, or knowledge work being disrupted by AI. A single quote from "
            "Dario Amodei or Sam Altman about consultants is MORE valuable than 10 "
            "articles from trade publications. Prioritize SIGNAL over NOISE — outside "
            "voices commenting on the industry are often more important than the "
            "industry talking about itself."
        ),
    ),
    ClientConfig(
        name="Logan Gott — Gott Content",
        industry="LinkedIn Content & B2B Copywriting",
        keywords=[
            "LinkedIn content strategy",
            "LinkedIn algorithm changes",
            "LinkedIn B2B marketing",
            "AI copywriting tools",
            "AI content writing",
            "SaaS content marketing",
            "B2B thought leadership",
            "LinkedIn ghostwriting",
            "AI SaaS marketing trends",
        ],
        entities=[
            "LinkedIn",
            "Jasper AI",
            "Copy.ai",
            "HubSpot",
        ],
        preferred_sources=[
            "linkedin.com",
            "socialmediatoday.com",
            "contentmarketinginstitute.com",
            "hbr.org",
            "techcrunch.com",
        ],
        focus_note=(
            "This client focuses ONLY on text-based LinkedIn content and B2B copywriting. "
            "EXCLUDE any articles about UGC, YouTube, video content, TikTok, Instagram Reels, "
            "or video production. Only include news relevant to written content, LinkedIn strategy, "
            "SaaS marketing, and AI writing tools."
        ),
    ),
]

# --- API Keys (set via environment variables) ---
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")

# The Notion page ID where weekly reports will be created as sub-pages
NOTION_PARENT_PAGE_ID = os.environ.get("NOTION_PARENT_PAGE_ID", "")

# --- Search settings ---
# How many days back to search (7 = one week)
LOOKBACK_DAYS = 7

# Max search results per query
MAX_RESULTS_PER_QUERY = 10

# Max total articles to include in the final report per client
MAX_ARTICLES_PER_REPORT = 15


def get_date_range() -> tuple[str, str]:
    """Return (start_date, end_date) strings for the past week."""
    end = datetime.now()
    start = end - timedelta(days=LOOKBACK_DAYS)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

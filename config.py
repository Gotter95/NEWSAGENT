"""
Central configuration — reads API keys from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_PARENT_PAGE_ID = os.environ["NOTION_PARENT_PAGE_ID"]

CLIENTS = {
    "Power Offer Consultants": {
        "queries": [
            "B2B irresistible offer strategy",
            "high-ticket consulting offer frameworks",
            "power offer positioning premium services",
            "value proposition consulting trends",
            "B2B sales offer optimization",
        ],
        "industry": "B2B consulting & offer strategy",
    },
    "Gott Content": {
        "queries": [
            "AI content creation tools trends",
            "content marketing strategy 2025",
            "AI video generation business",
            "short-form video marketing trends",
            "content agency scaling strategies",
        ],
        "industry": "AI-powered content creation & marketing",
    },
}

"""
Crawler configuration — centralizes settings that were previously hardcoded.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://postgres:postgres@localhost:5432/price_comparison",
)

# Scraping
BASE_URL = "https://glovoapp.com"
MAX_CONCURRENT_REQUESTS = 5
REQUEST_DELAY_SECONDS = 1.0
MIN_VALID_PRICE = 0.15
MAX_VALID_PRICE = 998.0

# Logging
LOG_FILE = os.getenv("CRAWLER_LOG_FILE", "crawler.log")
LOG_LEVEL = os.getenv("CRAWLER_LOG_LEVEL", "INFO")

# Supported stores and locations
AVAILABLE_STORES = ["penny", "conad", "deco", "crai", "coop", "dodeca"]
AVAILABLE_LOCATIONS = ["roma", "napoli"]

# HTTP headers
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

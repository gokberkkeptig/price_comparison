"""
Crawler configuration — settings for Open Food Facts & Open Prices APIs.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql://postgres:postgres@localhost:5432/price_comparison",
)

# Open Food Facts — Search-a-licious API (ElasticSearch-backed, fast & reliable)
OFF_SEARCH_URL = "https://search.openfoodfacts.org/search"
OFF_PRODUCT_FIELDS = "code,product_name,product_name_it,image_url,categories_tags,brands"
OFF_COUNTRY_TAG = "en:italy"
OFF_PAGE_SIZE = 50  # products per API page
OFF_MAX_PAGES = 4   # pages per subcategory → up to 200 products each

# Open Prices API
OPEN_PRICES_URL = "https://prices.openfoodfacts.org/api/v1"

# Rate limiting (be respectful to the free APIs)
REQUEST_DELAY_SECONDS = 1.0
MAX_CONCURRENT_REQUESTS = 3

# Price generation — used when Open Prices has no real data
# Base prices (EUR) for each subcategory; the crawler adds ±15 % store jitter
BASE_PRICES: dict[str, tuple[float, float]] = {
    # Dairy & Eggs
    "Milk":           (0.89, 1.89),
    "Cheese":         (1.50, 6.99),
    "Yogurt":         (0.49, 2.99),
    "Eggs":           (1.49, 3.49),
    # Bread & Bakery
    "Bread":          (0.79, 2.99),
    "Baked Goods":    (0.99, 3.49),
    # Pasta & Rice
    "Pasta":          (0.49, 2.49),
    "Rice":           (0.99, 3.49),
    # Meat & Fish
    "Fresh Meat":     (3.49, 12.99),
    "Cured Meats":    (1.49, 5.99),
    "Fresh Fish":     (4.99, 14.99),
    # Fruits & Vegetables
    "Fresh Fruits":   (0.99, 3.99),
    "Fresh Vegetables": (0.69, 3.49),
    # Beverages
    "Alcoholic Beverages":     (1.99, 12.99),
    "Non-Alcoholic Beverages": (0.49, 2.99),
    # Canned & Preserved
    "Canned Goods":        (0.69, 2.99),
    "Oils & Condiments":   (1.99, 7.99),
    # Snacks & Sweets
    "Snacks":              (0.99, 3.99),
    "Sweets & Chocolate":  (0.89, 4.99),
    "Ice Cream":           (1.99, 5.99),
    # Household & Personal Care
    "Cleaning Products":   (0.99, 4.99),
    "Personal Care":       (1.29, 5.99),
}

# Stores to simulate prices for
AVAILABLE_STORES = ["Penny", "Conad", "Coop", "Crai", "Decò", "Dodecà"]

# Locations
AVAILABLE_LOCATIONS = [
    {"city": "Roma", "country": "Italy"},
    {"city": "Napoli", "country": "Italy"},
    {"city": "Orvieto", "country": "Italy"},
    {"city": "Viterbo", "country": "Italy"},
]

# Logging
LOG_FILE = os.getenv("CRAWLER_LOG_FILE", "crawler.log")
LOG_LEVEL = os.getenv("CRAWLER_LOG_LEVEL", "INFO")

# HTTP headers — Open Food Facts asks for a descriptive User-Agent
USER_AGENT = "ComparazionePrezzi/1.0 (university project; contact@example.com)"

"""
Async product crawler for Glovo supermarket listings.

Scrapes product names, prices, and images from Glovo store pages
and upserts them into the shared PostgreSQL database.

Usage:
    python fast_crawler.py                           # scrape all stores in all locations
    python fast_crawler.py --stores penny conad      # specific stores
    python fast_crawler.py --locations roma           # specific location
    python fast_crawler.py --stores penny --locations napoli

Requirements:
    pip install aiohttp beautifulsoup4 sqlalchemy psycopg2-binary python-dotenv
"""

import asyncio
import argparse
import itertools
import logging
import os
import re
import sys
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path so we can import shared models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.models import (  # noqa: E402
    Store, Location, Category, SubCategory, Product, ProductPrice,
)
from app import db  # noqa: E402

from config import (  # noqa: E402
    DATABASE_URI, BASE_URL, MAX_CONCURRENT_REQUESTS,
    REQUEST_DELAY_SECONDS, MIN_VALID_PRICE, MAX_VALID_PRICE,
    LOG_FILE, LOG_LEVEL, USER_AGENT, AVAILABLE_STORES, AVAILABLE_LOCATIONS,
)
from category_mapping import find_category  # noqa: E402

# ---------------------------------------------------------------------------
# Database setup (standalone — not using Flask app context)
# ---------------------------------------------------------------------------
engine = create_engine(DATABASE_URI, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
def clean_product_name(name: str) -> str:
    """Remove trailing ' - number' suffixes from product names."""
    if not isinstance(name, str):
        return name
    return re.sub(r"\s*-\s*\d+$", "", name).strip()


def parse_price(price_text: str) -> float | None:
    """Parse a price string like '€1,99' into a float. Returns None on failure."""
    try:
        cleaned = price_text.replace("€", "").replace(",", ".").strip()
        price = float(cleaned)
        if MIN_VALID_PRICE <= price <= MAX_VALID_PRICE:
            return price
        return None
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Scraping functions
# ---------------------------------------------------------------------------
async def fetch(session: ClientSession, url: str) -> str:
    """Fetch a URL and return the response text."""
    headers = {"User-Agent": USER_AGENT}
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.text()


async def extract_subcategory_links(session: ClientSession, url: str) -> list[str]:
    """Extract subcategory page links from a store's main page."""
    try:
        html = await fetch(session, url)
        soup = BeautifulSoup(html, "html.parser")
        links = []

        for element in soup.find_all("div", class_="carousel__content__element"):
            a_tag = element.find("a", href=True)
            if a_tag:
                link = a_tag["href"]
                if not link.startswith("http"):
                    link = BASE_URL + link
                links.append(link)

        return links
    except Exception as e:
        logger.error("Error fetching subcategory links from %s: %s", url, e)
        return []


async def scrape_product_details(session: ClientSession, link: str) -> list[dict]:
    """Scrape all products from a subcategory page."""
    try:
        await asyncio.sleep(REQUEST_DELAY_SECONDS)
        html = await fetch(session, link)
        soup = BeautifulSoup(html, "html.parser")
        products = []

        for grid in soup.find_all("div", class_="grid"):
            # Extract the Italian subcategory name from the grid title
            title_el = grid.find("h2", class_="grid__title")
            italian_subcat = title_el.get_text(strip=True) if title_el else "N/A"

            # Map to English category/subcategory
            category_name, sub_category_name = find_category(italian_subcat)

            for tile in grid.find_all("div", class_="tile"):
                # Product name
                name_el = tile.find("span", class_="tile__description")
                raw_name = name_el.get_text(strip=True) if name_el else None
                if not raw_name:
                    continue
                name = clean_product_name(raw_name).title()

                # Price
                price_el = tile.find("span", class_="product-price__effective")
                price_text = price_el.get_text(strip=True) if price_el else None
                price = parse_price(price_text) if price_text else None
                if price is None:
                    continue

                # Image
                img_el = tile.find("img", class_="tile__image")
                image_url = img_el["src"] if img_el and img_el.get("src") else None

                products.append({
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "link": link,
                    "category": category_name,
                    "sub_category": sub_category_name,
                })

        logger.info("Scraped %d products from %s", len(products), link)
        return products

    except Exception as e:
        logger.error("Error scraping products from %s: %s", link, e)
        return []


# ---------------------------------------------------------------------------
# Database upsert
# ---------------------------------------------------------------------------
def upsert_product(db_session, product_data: dict, store_name: str, city: str) -> None:
    """Insert or update a product and its price in the database."""
    try:
        # Get or create Store
        store = db_session.query(Store).filter_by(name=store_name).first()
        if not store:
            store = Store(name=store_name)
            db_session.add(store)
            db_session.flush()

        # Get or create Location
        location = db_session.query(Location).filter_by(city=city).first()
        if not location:
            location = Location(city=city)
            db_session.add(location)
            db_session.flush()

        # Get or create Category
        category = db_session.query(Category).filter_by(name=product_data["category"]).first()
        if not category:
            category = Category(name=product_data["category"])
            db_session.add(category)
            db_session.flush()

        # Get or create SubCategory
        sub_category = db_session.query(SubCategory).filter_by(
            name=product_data["sub_category"],
            category_id=category.category_id,
        ).first()
        if not sub_category:
            sub_category = SubCategory(
                name=product_data["sub_category"],
                category_id=category.category_id,
            )
            db_session.add(sub_category)
            db_session.flush()

        # Get or create Product
        product = db_session.query(Product).filter_by(name=product_data["name"]).first()
        if not product:
            product = Product(
                name=product_data["name"],
                sub_category_id=sub_category.sub_category_id,
                link=product_data.get("link"),
                image_url=product_data.get("image_url"),
            )
            db_session.add(product)
            db_session.flush()
        else:
            # Update metadata if changed
            if product_data.get("link"):
                product.link = product_data["link"]
            if product_data.get("image_url"):
                product.image_url = product_data["image_url"]

        # Upsert ProductPrice
        product_price = db_session.query(ProductPrice).filter_by(
            product_id=product.product_id,
            store_id=store.store_id,
            location_id=location.location_id,
        ).first()

        now = datetime.now(timezone.utc)

        if not product_price:
            product_price = ProductPrice(
                product_id=product.product_id,
                store_id=store.store_id,
                location_id=location.location_id,
                price=product_data["price"],
                last_updated=now,
            )
            db_session.add(product_price)
        else:
            product_price.price = product_data["price"]
            product_price.last_updated = now

        db_session.commit()

    except Exception as e:
        db_session.rollback()
        logger.error("DB error for product '%s': %s", product_data.get("name"), e)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
async def scrape_store_location(store_name: str, location: str) -> None:
    """Scrape all products for a given store in a given location."""
    location_slug = location.lower()
    store_url = f"{BASE_URL}/it/it/{location_slug}/{store_name}-{location_slug[:3]}/"

    logger.info("Starting scrape: %s in %s (%s)", store_name, location, store_url)

    try:
        async with aiohttp.ClientSession() as session:
            subcategory_links = await extract_subcategory_links(session, store_url)
            logger.info("Found %d subcategories for %s in %s", len(subcategory_links), store_name, location)

            if not subcategory_links:
                logger.warning("No subcategories found — the page structure may have changed")
                return

            # Rate-limited concurrent scraping
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

            async def limited_scrape(link):
                async with semaphore:
                    return await scrape_product_details(session, link)

            tasks = [limited_scrape(link) for link in subcategory_links]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Flatten results, skip exceptions
            all_products = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error("Scraping task failed: %s", result)
                else:
                    all_products.extend(result)

            logger.info("Total products scraped for %s in %s: %d", store_name, location, len(all_products))

            # Persist to database using thread pool (avoid blocking event loop)
            with ThreadPoolExecutor(max_workers=5) as executor:
                loop = asyncio.get_running_loop()
                db_tasks = [
                    loop.run_in_executor(
                        executor,
                        upsert_product,
                        SessionLocal(),
                        product,
                        store_name,
                        location.capitalize(),
                    )
                    for product in all_products
                ]
                await asyncio.gather(*db_tasks, return_exceptions=True)

            logger.info("Data saved for %s in %s", store_name, location)

    except Exception as e:
        logger.error("Fatal error scraping %s in %s: %s", store_name, location, e)


async def main():
    parser = argparse.ArgumentParser(
        description="Scrape grocery product data from Glovo supermarket listings"
    )
    parser.add_argument(
        "--stores",
        nargs="+",
        choices=AVAILABLE_STORES,
        default=AVAILABLE_STORES,
        help="Stores to scrape (default: all)",
    )
    parser.add_argument(
        "--locations",
        nargs="+",
        choices=AVAILABLE_LOCATIONS,
        default=AVAILABLE_LOCATIONS,
        help="Locations to scrape (default: all)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Crawler started — stores: %s, locations: %s", args.stores, args.locations)
    logger.info("=" * 60)

    tasks = [
        scrape_store_location(store, location.capitalize())
        for store, location in itertools.product(args.stores, args.locations)
    ]
    await asyncio.gather(*tasks)

    logger.info("Crawler finished")


if __name__ == "__main__":
    asyncio.run(main())

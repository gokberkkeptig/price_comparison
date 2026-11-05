"""
Product crawler using Open Food Facts (Search-a-licious) + Open Prices APIs.

Fetches real Italian grocery products from Open Food Facts, looks up real
prices on Open Prices where available, and generates realistic simulated
prices for the remaining store/location combinations.

Usage:
    python fast_crawler.py                       # fetch all categories
    python fast_crawler.py --categories Pasta Rice Cheese
    python fast_crawler.py --max-pages 2         # fewer products (faster)

Requirements:
    pip install aiohttp sqlalchemy psycopg2-binary python-dotenv
"""

import asyncio
import argparse
import hashlib
import logging
import os
import random
import sys
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Imports from sibling packages
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.models import (  # noqa: E402
    Store, Location, Category, SubCategory, Product, ProductPrice,
)
from app import db as _flask_db  # noqa: E402  (imported so models resolve)

from config import (  # noqa: E402
    DATABASE_URI,
    OFF_SEARCH_URL, OFF_PRODUCT_FIELDS, OFF_COUNTRY_TAG,
    OFF_PAGE_SIZE, OFF_MAX_PAGES,
    OPEN_PRICES_URL,
    REQUEST_DELAY_SECONDS, MAX_CONCURRENT_REQUESTS,
    BASE_PRICES, AVAILABLE_STORES, AVAILABLE_LOCATIONS,
    LOG_FILE, LOG_LEVEL, USER_AGENT,
)
from category_mapping import CATEGORY_SEARCH_MAP, find_category  # noqa: E402

# ---------------------------------------------------------------------------
# Database (standalone — no Flask app context needed)
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

_console = logging.StreamHandler()
_console.setLevel(logging.INFO)
_console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(_console)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _deterministic_price(product_name: str, store: str, city: str,
                         low: float, high: float) -> float:
    """Generate a stable-but-varied price for a (product, store, city) triple."""
    seed = hashlib.md5(f"{product_name}|{store}|{city}".encode()).hexdigest()
    rng = random.Random(seed)
    base = rng.uniform(low, high)
    # Round to realistic grocery price (e.g. €1.49, €2.79)
    return round(round(base / 0.10) * 0.10 - 0.01, 2)


def _clean_name(name: str | None) -> str | None:
    """Title-case and strip whitespace."""
    if not name:
        return None
    return name.strip().title()


# ---------------------------------------------------------------------------
# Open Food Facts — fetch products via Search-a-licious
# ---------------------------------------------------------------------------
async def fetch_off_products(
    session: aiohttp.ClientSession,
    off_tag: str,
    max_pages: int,
) -> list[dict]:
    """
    Search Open Food Facts for Italian products in the given category tag
    using the Search-a-licious ElasticSearch API.
    Returns a flat list of simplified product dicts.
    """
    products: list[dict] = []
    headers = {"User-Agent": USER_AGENT}

    for page in range(1, max_pages + 1):
        # Search-a-licious uses Lucene query syntax
        q = f'categories_tags:"en:{off_tag}" countries_tags:"{OFF_COUNTRY_TAG}"'
        params = {
            "q": q,
            "page_size": OFF_PAGE_SIZE,
            "page": page,
            "fields": OFF_PRODUCT_FIELDS,
            "langs": "it,en",
        }
        try:
            await asyncio.sleep(REQUEST_DELAY_SECONDS)
            async with session.get(OFF_SEARCH_URL, params=params, headers=headers) as resp:
                if resp.status != 200:
                    logger.warning("OFF returned %s for tag=%s page=%s", resp.status, off_tag, page)
                    break
                data = await resp.json()
        except Exception as e:
            logger.error("OFF request failed for tag=%s page=%s: %s", off_tag, page, e)
            break

        # Search-a-licious returns results in "hits" (not "products")
        page_products = data.get("hits", [])
        if not page_products:
            break

        for p in page_products:
            name = p.get("product_name_it") or p.get("product_name")
            if not name or len(name) < 2:
                continue

            # brands can be a list or a string
            brands = p.get("brands", "")
            if isinstance(brands, list):
                brands = ", ".join(brands)

            products.append({
                "code": p.get("code"),
                "name": _clean_name(name),
                "image_url": p.get("image_url"),
                "brands": brands,
                "categories_tags": p.get("categories_tags", []),
                "link": f"https://world.openfoodfacts.org/product/{p.get('code', '')}",
            })

        logger.info("OFF tag=%s page=%d → %d products", off_tag, page, len(page_products))

    return products


# ---------------------------------------------------------------------------
# Open Prices — look up real prices (best-effort)
# ---------------------------------------------------------------------------
async def fetch_open_prices(
    session: aiohttp.ClientSession,
    product_code: str,
) -> list[dict]:
    """Fetch real prices for a barcode from the Open Prices API."""
    url = f"{OPEN_PRICES_URL}/prices"
    params = {
        "product_code": product_code,
        "currency": "EUR",
        "page_size": 10,
        "order_by": "-date",
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            return data.get("items", [])
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Database upsert (runs in thread pool — no async)
# ---------------------------------------------------------------------------
def _get_or_create(db_session, model, defaults=None, **kwargs):
    """Thread-safe get-or-create: try SELECT first, INSERT on miss, SELECT on conflict."""
    instance = db_session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    try:
        instance = model(**kwargs, **(defaults or {}))
        db_session.add(instance)
        db_session.flush()
        return instance
    except Exception:
        db_session.rollback()
        instance = db_session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        raise


def upsert_product(
    product_data: dict,
    category_name: str,
    sub_category_name: str,
    store_name: str,
    city: str,
    country: str,
    price: float,
) -> None:
    """Insert or update one product + one price row."""
    db_session = SessionLocal()
    try:
        store = _get_or_create(db_session, Store, name=store_name)
        location = _get_or_create(db_session, Location, city=city, country=country)
        category = _get_or_create(db_session, Category, name=category_name)
        sub_category = _get_or_create(
            db_session, SubCategory,
            name=sub_category_name, category_id=category.category_id,
        )

        # Product (unique by name + sub_category)
        product = _get_or_create(
            db_session, Product,
            defaults={
                "link": product_data.get("link"),
                "image_url": product_data.get("image_url"),
            },
            name=product_data["name"],
            sub_category_id=sub_category.sub_category_id,
        )
        # Update metadata if product already existed
        if product_data.get("image_url"):
            product.image_url = product_data["image_url"]
        if product_data.get("link"):
            product.link = product_data["link"]

        # Price (unique by product + store + location)
        pp = db_session.query(ProductPrice).filter_by(
            product_id=product.product_id,
            store_id=store.store_id,
            location_id=location.location_id,
        ).first()

        now = datetime.now(timezone.utc)
        if not pp:
            pp = ProductPrice(
                product_id=product.product_id,
                store_id=store.store_id,
                location_id=location.location_id,
                price=price,
                last_updated=now,
            )
            db_session.add(pp)
        else:
            pp.price = price
            pp.last_updated = now

        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error("DB error for '%s' @ %s/%s: %s", product_data.get("name"), store_name, city, e)
    finally:
        db_session.close()


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
async def process_subcategory(
    http: aiohttp.ClientSession,
    cat_name: str,
    subcat_name: str,
    off_tags: list[str],
    max_pages: int,
    semaphore: asyncio.Semaphore,
) -> int:
    """Fetch products for one subcategory, resolve prices, persist."""
    all_products: list[dict] = []

    for tag in off_tags:
        async with semaphore:
            prods = await fetch_off_products(http, tag, max_pages)
            all_products.extend(prods)

    # Deduplicate by product code
    seen_codes: set[str] = set()
    unique: list[dict] = []
    for p in all_products:
        code = p.get("code")
        if code and code not in seen_codes:
            seen_codes.add(code)
            unique.append(p)
        elif not code:
            unique.append(p)
    all_products = unique

    if not all_products:
        logger.warning("No products found for %s > %s", cat_name, subcat_name)
        return 0

    logger.info("Processing %d products for %s > %s", len(all_products), cat_name, subcat_name)

    # Price range for this subcategory
    price_low, price_high = BASE_PRICES.get(subcat_name, (0.99, 4.99))

    # Try to get real prices from Open Prices for a sample of products
    real_prices: dict[str, float] = {}  # code → EUR price
    sample = all_products[:20]  # limit API calls
    for p in sample:
        code = p.get("code")
        if not code:
            continue
        async with semaphore:
            await asyncio.sleep(0.5)
            items = await fetch_open_prices(http, code)
        for item in items:
            if item.get("price") and item["price"] > 0:
                real_prices[code] = item["price"]
                break  # one price per product is enough

    if real_prices:
        logger.info("Found %d real prices from Open Prices for %s > %s",
                     len(real_prices), cat_name, subcat_name)

    # Persist to DB — generate a price per (product, store, location)
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=5) as pool:
        tasks = []
        for product_data in all_products:
            for store_name in AVAILABLE_STORES:
                for loc in AVAILABLE_LOCATIONS:
                    code = product_data.get("code", "")
                    if code in real_prices:
                        # Use real price + small store/location jitter (±8 %)
                        jitter_seed = f"{code}|{store_name}|{loc['city']}"
                        rng = random.Random(hashlib.md5(jitter_seed.encode()).hexdigest())
                        price = round(real_prices[code] * rng.uniform(0.92, 1.08), 2)
                    else:
                        price = _deterministic_price(
                            product_data["name"], store_name, loc["city"],
                            price_low, price_high,
                        )

                    tasks.append(loop.run_in_executor(
                        pool,
                        upsert_product,
                        product_data, cat_name, subcat_name,
                        store_name, loc["city"], loc["country"],
                        price,
                    ))

        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Saved %s > %s (%d products × %d stores × %d locations)",
                cat_name, subcat_name, len(all_products),
                len(AVAILABLE_STORES), len(AVAILABLE_LOCATIONS))

    return len(all_products)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch grocery products from Open Food Facts")
    parser.add_argument(
        "--categories", nargs="+", default=None,
        help="SubCategory names to fetch (default: all). E.g. --categories Pasta Cheese Milk",
    )
    parser.add_argument(
        "--max-pages", type=int, default=OFF_MAX_PAGES,
        help=f"Max OFF pages per subcategory (default: {OFF_MAX_PAGES})",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Crawler started — source: Open Food Facts + Open Prices")
    logger.info("=" * 60)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    total = 0

    async with aiohttp.ClientSession() as http:
        for (cat, subcat), off_tags in CATEGORY_SEARCH_MAP.items():
            if args.categories and subcat not in args.categories:
                continue
            count = await process_subcategory(
                http, cat, subcat, off_tags, args.max_pages, semaphore,
            )
            total += count

    logger.info("=" * 60)
    logger.info("Crawler finished — %d unique products processed", total)
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

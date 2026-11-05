"""
Maps Open Food Facts category tags (English) to the app's Category → SubCategory hierarchy.

Each entry maps:
    (app_category, app_subcategory) → list of OFF categories_tags_en values to search for.

The crawler iterates this mapping to fetch products from the OFF API.
"""

# OFF tag → (our Category, our SubCategory)
# We search OFF by the first tag in each list; extras are used for classification fallback.
CATEGORY_SEARCH_MAP: dict[tuple[str, str], list[str]] = {
    # ── Dairy & Eggs ──────────────────────────────────────────────
    ("Dairy & Eggs", "Milk"):    ["milks"],
    ("Dairy & Eggs", "Cheese"):  ["cheeses"],
    ("Dairy & Eggs", "Yogurt"):  ["yogurts"],
    ("Dairy & Eggs", "Eggs"):    ["eggs"],

    # ── Bread & Bakery ────────────────────────────────────────────
    ("Bread & Bakery", "Bread"):       ["breads"],
    ("Bread & Bakery", "Baked Goods"): ["biscuits", "pastries"],

    # ── Pasta & Rice ──────────────────────────────────────────────
    ("Pasta & Rice", "Pasta"):  ["pastas"],
    ("Pasta & Rice", "Rice"):   ["rices"],

    # ── Meat & Fish ───────────────────────────────────────────────
    ("Meat & Fish", "Fresh Meat"):  ["meats"],
    ("Meat & Fish", "Cured Meats"): ["sausages", "hams"],
    ("Meat & Fish", "Fresh Fish"):  ["fishes"],

    # ── Fruits & Vegetables ───────────────────────────────────────
    ("Fruits & Vegetables", "Fresh Fruits"):     ["fruits"],
    ("Fruits & Vegetables", "Fresh Vegetables"): ["vegetables"],

    # ── Beverages ─────────────────────────────────────────────────
    ("Beverages", "Alcoholic Beverages"):     ["wines", "beers"],
    ("Beverages", "Non-Alcoholic Beverages"): ["fruit-juices", "waters", "soft-drinks"],

    # ── Canned & Preserved ────────────────────────────────────────
    ("Canned & Preserved", "Canned Goods"):      ["canned-foods"],
    ("Canned & Preserved", "Oils & Condiments"): ["olive-oils", "vinegars", "sauces"],

    # ── Snacks & Sweets ───────────────────────────────────────────
    ("Snacks & Sweets", "Snacks"):             ["chips-and-fries", "nuts"],
    ("Snacks & Sweets", "Sweets & Chocolate"): ["chocolates", "candies"],
    ("Snacks & Sweets", "Ice Cream"):          ["ice-creams"],

    # ── Household & Personal Care ─────────────────────────────────
    # OFF has very few non-food items, so we use broader tags
    ("Household & Personal Care", "Cleaning Products"): ["cleaning-products"],
    ("Household & Personal Care", "Personal Care"):     ["body-care"],
}


def find_category(off_categories_tags: list[str]) -> tuple[str, str]:
    """
    Given a product's categories_tags list from OFF, return the best
    (Category, SubCategory) match from our schema.

    Falls back to ("Uncategorized", "Uncategorized").
    """
    if not off_categories_tags:
        return "Uncategorized", "Uncategorized"

    # Build a set of the tag leaves (e.g. "en:milks" → "milks")
    tag_leaves = {t.split(":")[-1] for t in off_categories_tags}

    for (cat, subcat), search_tags in CATEGORY_SEARCH_MAP.items():
        for tag in search_tags:
            if tag in tag_leaves:
                return cat, subcat

    return "Uncategorized", "Uncategorized"

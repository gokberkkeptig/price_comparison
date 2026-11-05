from flask import Blueprint, request, jsonify

from app import db
from app.models import (
    Product, ProductPrice, Store, Location, Category, SubCategory,
)
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import joinedload

products_bp = Blueprint("products", __name__)


@products_bp.route("", methods=["GET"])
def list_products():
    """List products with search, filters, ordering, and pagination."""
    query_str = request.args.get("query", "").strip()
    order_by = request.args.get("order_by", "asc").strip()
    category_filter = request.args.get("category", "").strip()
    store_filter = request.args.get("store", "").strip()
    city_filter = request.args.get("city", "").strip()

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except (ValueError, TypeError):
        per_page = 20

    # Base query
    products_query = (
        db.session.query(Product, func.min(ProductPrice.price).label("min_price"))
        .join(ProductPrice)
        .join(Store, ProductPrice.store_id == Store.store_id)
        .join(SubCategory, Product.sub_category_id == SubCategory.sub_category_id)
        .join(Category, SubCategory.category_id == Category.category_id)
        .join(Location, ProductPrice.location_id == Location.location_id)
    )

    # Apply city filter
    if city_filter:
        products_query = products_query.filter(Location.city.ilike(city_filter))

    # Full-text search (PostgreSQL)
    if query_str:
        search_vector = func.to_tsvector(
            "english", func.concat_ws(" ", Product.name, SubCategory.name, Category.name)
        )
        search_query = func.plainto_tsquery("english", query_str)
        products_query = products_query.filter(search_vector.op("@@")(search_query))

    # Category filter
    if category_filter:
        products_query = products_query.filter(Category.name.ilike(category_filter))

    # Store filter
    if store_filter:
        products_query = products_query.filter(Store.name.ilike(store_filter))

    # Group and order
    products_query = products_query.group_by(Product.product_id)

    if order_by == "desc":
        products_query = products_query.order_by(desc("min_price"))
    else:
        products_query = products_query.order_by(asc("min_price"))

    # Paginate
    total = products_query.count()
    results = products_query.offset((page - 1) * per_page).limit(per_page).all()

    products_data = []
    for product, min_price in results:
        data = product.to_dict(include_prices=False)
        data["min_price"] = min_price
        products_data.append(data)

    return jsonify({
        "products": products_data,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page,
    }), 200


@products_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Get a single product with all its prices."""
    product = Product.query.options(
        joinedload(Product.sub_category).joinedload(SubCategory.category),
        joinedload(Product.prices).joinedload(ProductPrice.store),
        joinedload(Product.prices).joinedload(ProductPrice.location),
    ).get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({"product": product.to_dict(include_prices=True)}), 200


@products_bp.route("/categories", methods=["GET"])
def list_categories():
    """List all categories."""
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify({"categories": [c.to_dict() for c in categories]}), 200


@products_bp.route("/stores", methods=["GET"])
def list_stores():
    """List all stores."""
    stores = Store.query.order_by(Store.name.asc()).all()
    return jsonify({"stores": [s.to_dict() for s in stores]}), 200


@products_bp.route("/locations", methods=["GET"])
def list_locations():
    """List all locations."""
    locations = Location.query.order_by(Location.city.asc()).all()
    return jsonify({"locations": [l.to_dict() for l in locations]}), 200

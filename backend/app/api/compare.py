from flask import Blueprint, request, jsonify

from app.models import Product, ProductPrice, SubCategory
from sqlalchemy.orm import joinedload

compare_bp = Blueprint("compare", __name__)


@compare_bp.route("/compare", methods=["GET"])
def compare_products():
    """Compare up to 4 products side by side."""
    ids_param = request.args.get("ids", "")
    if not ids_param:
        return jsonify({"error": "Provide product IDs via ?ids=1,2,3"}), 400

    try:
        product_ids = [int(x.strip()) for x in ids_param.split(",") if x.strip()]
    except ValueError:
        return jsonify({"error": "Product IDs must be integers"}), 400

    if len(product_ids) > 4:
        return jsonify({"error": "You can compare up to 4 products at a time"}), 400

    if not product_ids:
        return jsonify({"error": "At least one product ID is required"}), 400

    products = Product.query.options(
        joinedload(Product.sub_category).joinedload(SubCategory.category),
        joinedload(Product.prices).joinedload(ProductPrice.store),
        joinedload(Product.prices).joinedload(ProductPrice.location),
    ).filter(Product.product_id.in_(product_ids)).all()

    if not products:
        return jsonify({"error": "No products found"}), 404

    products_data = []
    cheapest_id = None
    cheapest_price = None

    for product in products:
        data = product.to_dict(include_prices=True)
        products_data.append(data)

        if data["min_price"] is not None:
            if cheapest_price is None or data["min_price"] < cheapest_price:
                cheapest_price = data["min_price"]
                cheapest_id = product.product_id

    return jsonify({
        "products": products_data,
        "cheapest_product_id": cheapest_id,
    }), 200

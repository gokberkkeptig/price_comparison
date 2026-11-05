from flask import Blueprint, request, jsonify

from app.models import Product, Store

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/calculate", methods=["POST"])
def calculate_cart():
    """
    Calculate total cart cost per store.
    
    Expects JSON body:
    {
        "cart": {"product_id": quantity, ...}
    }
    
    Returns cost breakdown per store and identifies the cheapest store.
    """
    data = request.get_json()
    if not data or "cart" not in data:
        return jsonify({"error": "Cart data is required"}), 400

    cart = data["cart"]
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    try:
        product_ids = [int(pid) for pid in cart.keys()]
        quantities = {int(pid): int(qty) for pid, qty in cart.items()}
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid cart format"}), 400

    products = Product.query.filter(Product.product_id.in_(product_ids)).all()
    if not products:
        return jsonify({"error": "No products found"}), 404

    # Get all stores
    stores = Store.query.all()
    store_names = [s.name for s in stores]

    # Build product data and calculate per-store totals
    products_data = []
    store_totals = {s.name: 0.0 for s in stores}
    store_availability = {s.name: 0 for s in stores}

    for product in products:
        qty = quantities.get(product.product_id, 1)
        product_info = {
            "product_id": product.product_id,
            "name": product.name,
            "image_url": product.image_url,
            "quantity": qty,
            "prices": [],
        }

        for price in product.prices:
            store_name = price.store.name
            product_info["prices"].append({
                "store": store_name,
                "price": price.price,
                "subtotal": price.price * qty,
            })
            store_totals[store_name] += price.price * qty
            store_availability[store_name] += 1

        products_data.append(product_info)

    total_items = len(products)

    # Build store summaries (only stores that have at least one product)
    store_summaries = []
    for store_name in store_names:
        if store_availability[store_name] > 0:
            store_summaries.append({
                "store": store_name,
                "total": round(store_totals[store_name], 2),
                "available_products": store_availability[store_name],
                "total_products": total_items,
                "complete": store_availability[store_name] == total_items,
            })

    # Sort by total price
    store_summaries.sort(key=lambda x: x["total"])

    cheapest_store = store_summaries[0]["store"] if store_summaries else None

    return jsonify({
        "products": products_data,
        "store_summaries": store_summaries,
        "cheapest_store": cheapest_store,
        "stores": store_names,
    }), 200

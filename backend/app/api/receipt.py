import base64
import io
import json
import re
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from app import db
from app.models import (
    Product, ProductPrice, Store, Location, Category, SubCategory,
)

receipt_bp = Blueprint("receipt", __name__)


def _parse_receipt_with_llm(extracted_text: str) -> dict:
    """Use Ollama LLM to parse receipt text into structured data."""
    try:
        from langchain_ollama import OllamaLLM
    except ImportError:
        raise RuntimeError(
            "langchain_ollama is not installed. Install it with: pip install langchain-ollama"
        )

    prompt = (
        "You are tasked with extracting specific information from the following text of a receipt. "
        "You need to extract:\n"
        "- The name of the supermarket ('store_name')\n"
        "- The date of the receipt ('date')\n"
        "- The list of items ('items') with their names ('name') and prices ('price')\n\n"
        "Here is the text of the receipt:\n"
        f"{extracted_text}\n\n"
        "Please follow these instructions carefully:\n"
        "1. Do not include any extra text, comments, or explanations in your response.\n"
        "2. Completely ignore lines that contain the words 'sconto' or 'C.Insieme'.\n"
        "3. If you cannot find some of the required information, leave that field empty.\n"
        "4. Provide the result in JSON format with keys 'store_name', 'date', and 'items'.\n"
        "5. The 'items' key should be a list of objects, each with 'name' and 'price'.\n"
        "6. The 'price' should be a decimal number using a dot as decimal separator.\n"
        "7. When the store name is unclear, use famous Italian supermarkets (e.g., CONAD, PENNY).\n"
        "8. Use date format 'dd/mm/yyyy'.\n"
        "9. Example output:\n"
        '{"store_name": "CONAD", "date": "09/09/2024", "items": [{"name": "BIRBE RINGS AMADORI", "price": 4.99}]}\n'
    )

    model = OllamaLLM(model="llama3.2")
    response = model.invoke(input=prompt)

    return json.loads(response)


@receipt_bp.route("/scan", methods=["POST"])
def scan_receipt():
    """
    Process a receipt image: OCR + LLM parsing + DB update.
    
    Expects JSON body with base64-encoded image:
    {"image": "data:image/png;base64,..."}
    """
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "Image data is required"}), 400

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return jsonify({
            "error": "OCR dependencies not installed. Install: pip install pytesseract Pillow"
        }), 500

    image_data = data["image"]
    # Remove base64 header if present
    image_data = re.sub(r"^data:image/.+;base64,", "", image_data)

    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return jsonify({"error": "Invalid image data"}), 400

    # OCR
    extracted_text = pytesseract.image_to_string(image, lang="ita")
    if not extracted_text.strip():
        return jsonify({"error": "No text detected in the image"}), 400

    # LLM parsing
    try:
        receipt_data = _parse_receipt_with_llm(extracted_text)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse receipt data"}), 500
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    # Process receipt data into the database
    feedback = []

    # Store
    store_name = (receipt_data.get("store_name") or "Unknown").strip().lower()
    store = Store.query.filter_by(name=store_name).first()
    if not store:
        store = Store(name=store_name)
        db.session.add(store)
        db.session.flush()

    # Date
    receipt_date_str = receipt_data.get("date", "").strip()
    try:
        receipt_date = datetime.strptime(receipt_date_str, "%d/%m/%Y").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        receipt_date = datetime.now(timezone.utc)

    # Default category/subcategory for receipt items
    category = Category.query.filter_by(name="Uncategorized").first()
    if not category:
        category = Category(name="Uncategorized")
        db.session.add(category)
        db.session.flush()

    sub_category = SubCategory.query.filter_by(
        name="Uncategorized", category_id=category.category_id
    ).first()
    if not sub_category:
        sub_category = SubCategory(name="Uncategorized", category_id=category.category_id)
        db.session.add(sub_category)
        db.session.flush()

    # Default location
    location = Location.query.filter_by(city="Roma", country="Italy").first()
    if not location:
        location = Location(city="Roma", country="Italy")
        db.session.add(location)
        db.session.flush()

    # Process items
    for item in receipt_data.get("items", []):
        product_name = (item.get("name") or "").strip().title()
        if not product_name:
            continue

        try:
            price = float(item.get("price", 0))
        except (ValueError, TypeError):
            feedback.append(f"Invalid price for '{product_name}', skipped")
            continue

        product = Product.query.filter_by(name=product_name).first()
        if not product:
            product = Product(
                name=product_name,
                sub_category_id=sub_category.sub_category_id,
            )
            db.session.add(product)
            db.session.flush()
            feedback.append(f"New product '{product_name}' added")

        product_price = ProductPrice.query.filter_by(
            product_id=product.product_id,
            store_id=store.store_id,
            location_id=location.location_id,
        ).first()

        if product_price:
            if product_price.last_updated < receipt_date:
                product_price.price = price
                product_price.last_updated = receipt_date
                feedback.append(f"Price updated for '{product_name}'")
            else:
                feedback.append(f"Existing price for '{product_name}' is more recent, skipped")
        else:
            product_price = ProductPrice(
                product_id=product.product_id,
                store_id=store.store_id,
                location_id=location.location_id,
                price=price,
                last_updated=receipt_date,
            )
            db.session.add(product_price)
            feedback.append(f"New price for '{product_name}' at {store_name}")

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Database operation failed"}), 500

    return jsonify({
        "message": "Receipt processed successfully",
        "receipt": receipt_data,
        "feedback": feedback,
    }), 200

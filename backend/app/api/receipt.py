import base64
import io
import json
import os
import re
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from app import db
from app.models import (
    Product, ProductPrice, Store, Location, Category, SubCategory,
)

receipt_bp = Blueprint("receipt", __name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def _parse_receipt_with_llm(extracted_text: str) -> dict:
    """Use Ollama LLM to parse receipt text into structured data."""
    from langchain_ollama import OllamaLLM

    prompt = (
        "You are an expert at reading Italian supermarket receipts. "
        "Extract structured data from the following OCR text.\n\n"
        "Extract:\n"
        "- store_name: The supermarket name (e.g. CONAD, PENNY, COOP, CRAI, DECÒ, DODECÀ, EUROSPIN)\n"
        "- city: The city where the store is located (look for address info)\n"
        "- date: The receipt date in dd/mm/yyyy format\n"
        "- items: A list of products with 'name' (product name) and 'price' (as decimal number with dot)\n\n"
        "Rules:\n"
        "1. Return ONLY valid JSON, no extra text or markdown.\n"
        "2. Ignore lines with 'sconto', 'TOTALE', 'CONTANTE', 'RESTO', 'IVA', 'C.Insieme', 'SUBTOTALE'.\n"
        "3. Price must use dot as decimal separator (e.g. 4.99).\n"
        "4. Clean up product names: remove codes, asterisks, and extra whitespace.\n"
        "5. If store_name or city is unclear, use empty string.\n"
        "6. If date is unclear, use empty string.\n\n"
        f"OCR Text:\n{extracted_text}\n\n"
        "JSON:"
    )

    model = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    response = model.invoke(input=prompt)

    # Extract JSON from the response
    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if not json_match:
        raise json.JSONDecodeError("No JSON found in LLM response", response, 0)

    return json.loads(json_match.group())


# ──────────────────────────────────────────────────────────────────
# Step 1: Analyze — OCR + LLM, return results without saving
# ──────────────────────────────────────────────────────────────────
@receipt_bp.route("/scan", methods=["POST"])
def scan_receipt():
    """
    Phase 1: OCR + LLM analysis only. Returns extracted data for user review.
    Phase 2 (confirm) saves to DB.

    Body: { "image": "data:image/...;base64,..." }
    """
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "Image data is required"}), 400

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return jsonify({"error": "OCR deps not installed (pytesseract, Pillow)"}), 500

    # Decode image
    image_data = re.sub(r"^data:image/.+;base64,", "", data["image"])
    try:
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return jsonify({"error": "Invalid image data"}), 400

    # OCR
    try:
        extracted_text = pytesseract.image_to_string(image, lang="ita")
    except Exception as e:
        return jsonify({"error": f"OCR failed: {e}"}), 500

    if not extracted_text.strip():
        return jsonify({"error": "Nessun testo rilevato nell'immagine"}), 400

    # LLM parsing
    try:
        receipt_data = _parse_receipt_with_llm(extracted_text)
    except json.JSONDecodeError:
        return jsonify({
            "error": "Il modello non è riuscito a estrarre dati strutturati. Riprova con un'immagine più nitida.",
            "ocr_text": extracted_text[:1000],
        }), 422
    except Exception as e:
        return jsonify({
            "error": f"Errore LLM: {e}. Ollama è in esecuzione?",
            "ocr_text": extracted_text[:1000],
        }), 500

    # Return data for review — NOT saved yet
    return jsonify({
        "status": "review",
        "message": "Dati estratti. Verifica e conferma per salvare nel database.",
        "receipt": receipt_data,
        "ocr_text": extracted_text[:1500],
    }), 200


# ──────────────────────────────────────────────────────────────────
# Step 2: Confirm — save reviewed data to DB
# ──────────────────────────────────────────────────────────────────
@receipt_bp.route("/confirm", methods=["POST"])
def confirm_receipt():
    """
    Save reviewed receipt data to the database.

    Body: {
        "store_name": "Conad",
        "city": "Roma",
        "date": "09/09/2024",
        "items": [{"name": "Pasta Barilla", "price": 1.29}, ...]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    store_name = (data.get("store_name") or "").strip().capitalize()
    city = (data.get("city") or "").strip().capitalize()
    date_str = (data.get("date") or "").strip()
    items = data.get("items", [])

    if not store_name:
        return jsonify({"error": "Nome supermercato richiesto"}), 400
    if not city:
        return jsonify({"error": "Città richiesta"}), 400
    if not items:
        return jsonify({"error": "Nessun prodotto da salvare"}), 400

    feedback = []

    # Store — get or create
    store = Store.query.filter(db.func.lower(Store.name) == store_name.lower()).first()
    if not store:
        store = Store(name=store_name)
        db.session.add(store)
        db.session.flush()
        feedback.append(f"Nuovo supermercato '{store_name}' creato")

    # Location — get or create
    location = Location.query.filter(db.func.lower(Location.city) == city.lower()).first()
    if not location:
        location = Location(city=city, country="Italy")
        db.session.add(location)
        db.session.flush()
        feedback.append(f"Nuova città '{city}' aggiunta")

    # Date
    try:
        receipt_date = datetime.strptime(date_str, "%d/%m/%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        receipt_date = datetime.now(timezone.utc)

    # Uncategorized fallback
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

    # Process items
    saved = 0
    for item in items:
        product_name = (item.get("name") or "").strip().title()
        if not product_name or len(product_name) < 2:
            continue

        try:
            price = round(float(item.get("price", 0)), 2)
            if price <= 0:
                continue
        except (ValueError, TypeError):
            feedback.append(f"Prezzo non valido per '{product_name}', ignorato")
            continue

        # Find or create product
        product = Product.query.filter(
            db.func.lower(Product.name) == product_name.lower()
        ).first()
        if not product:
            product = Product(
                name=product_name,
                sub_category_id=sub_category.sub_category_id,
            )
            db.session.add(product)
            db.session.flush()
            feedback.append(f"Nuovo prodotto '{product_name}' aggiunto")

        # Upsert price
        pp = ProductPrice.query.filter_by(
            product_id=product.product_id,
            store_id=store.store_id,
            location_id=location.location_id,
        ).first()

        if pp:
            if pp.last_updated is None or pp.last_updated < receipt_date:
                pp.price = price
                pp.last_updated = receipt_date
                feedback.append(f"Prezzo aggiornato: '{product_name}' → €{price:.2f}")
                saved += 1
            else:
                feedback.append(f"Prezzo esistente per '{product_name}' è più recente")
        else:
            pp = ProductPrice(
                product_id=product.product_id,
                store_id=store.store_id,
                location_id=location.location_id,
                price=price,
                last_updated=receipt_date,
            )
            db.session.add(pp)
            feedback.append(f"Nuovo prezzo: '{product_name}' @ {store_name} ({city}) → €{price:.2f}")
            saved += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Errore database: {e}"}), 500

    return jsonify({
        "message": f"Salvato: {saved} prezzi aggiunti/aggiornati su {len(items)} prodotti",
        "feedback": feedback,
    }), 200

"""
Seed script — populates the database with realistic Italian grocery data.

Usage:
    python seed.py          # seed the database
    python seed.py --reset  # drop and recreate all tables first

Idempotent: running multiple times won't duplicate data (uses get-or-create).
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta, timezone

# Make sure the app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Store, Location, Category, SubCategory, Product, ProductPrice

# ---------------------------------------------------------------------------
# Data definitions
# ---------------------------------------------------------------------------

STORES = ["conad", "penny", "coop", "crai", "deco", "dodeca"]

LOCATIONS = [
    {"city": "Roma", "country": "Italy"},
    {"city": "Napoli", "country": "Italy"},
]

# Categories → SubCategories → Products (name, base_price)
CATALOG = {
    "Beverages": {
        "Alcoholic Beverages": [
            ("Peroni Nastro Azzurro 66cl", 1.49),
            ("Moretti Birra 33cl", 0.99),
            ("Ichnusa Non Filtrata 50cl", 1.89),
            ("Prosecco Valdobbiadene DOC 75cl", 7.99),
            ("Chianti Classico DOCG 75cl", 6.49),
            ("Montepulciano d'Abruzzo DOC 75cl", 4.99),
            ("Aperol 70cl", 9.99),
            ("Campari 70cl", 10.49),
            ("Limoncello di Sorrento 50cl", 8.99),
            ("Sambuca Molinari 70cl", 11.99),
        ],
        "Non-Alcoholic Beverages": [
            ("Acqua Naturale Sant'Anna 1.5L", 0.35),
            ("Acqua Frizzante San Pellegrino 1L", 0.65),
            ("Coca-Cola 1.5L", 1.59),
            ("Fanta Aranciata 1.5L", 1.49),
            ("Succo ACE Yoga 1L", 1.29),
            ("Estathé Pesca 3x200ml", 1.69),
            ("Chinotto San Pellegrino 4x20cl", 2.99),
            ("Succo Santal Arancia Rossa 1L", 1.39),
            ("Acqua Tonica Schweppes 4x18cl", 2.89),
            ("Limonata Lurisia 27.5cl", 1.49),
        ],
        "Coffee & Tea": [
            ("Lavazza Qualità Rossa 250g", 3.49),
            ("Illy Classico Macinato 250g", 5.99),
            ("Caffè Kimbo Napoletano 250g", 3.29),
            ("Caffè Borbone Cialde ESE x50", 9.99),
            ("Tè Twinings Earl Grey 25 bustine", 3.19),
            ("Camomilla Bonomelli 14 filtri", 2.49),
        ],
    },
    "Dairy & Eggs": {
        "Milk": [
            ("Latte Intero Granarolo 1L", 1.39),
            ("Latte Parzialmente Scremato Parmalat 1L", 1.29),
            ("Latte Fresco Alta Qualità 1L", 1.69),
            ("Latte di Mandorla Condorelli 1L", 2.29),
            ("Latte Senza Lattosio Zymil 1L", 1.59),
        ],
        "Cheese": [
            ("Parmigiano Reggiano DOP 200g", 4.99),
            ("Mozzarella di Bufala DOP 125g", 2.49),
            ("Gorgonzola Dolce DOP 200g", 2.99),
            ("Pecorino Romano DOP 200g", 4.49),
            ("Burrata Pugliese 200g", 3.29),
            ("Ricotta Fresca 250g", 1.59),
            ("Scamorza Affumicata 250g", 2.89),
            ("Mascarpone Galbani 250g", 1.99),
        ],
        "Yogurt": [
            ("Müller Yogurt Bianco 125g", 0.59),
            ("Activia Naturale 4x125g", 2.49),
            ("Yogurt Greco Fage 0% 170g", 1.29),
            ("Yogurt Vipiteno Fragola 125g", 0.69),
        ],
        "Eggs": [
            ("Uova Fresche Medie x6", 1.49),
            ("Uova Biologiche Allevamento a Terra x6", 2.49),
            ("Uova Grandi x10", 2.99),
        ],
    },
    "Bread & Bakery": {
        "Bread": [
            ("Pane Casereccio 500g", 1.49),
            ("Pane Integrale 400g", 1.79),
            ("Ciabatta Classica 250g", 1.19),
            ("Focaccia Genovese 300g", 2.49),
            ("Pane di Altamura DOP 500g", 2.29),
            ("Panini al Latte x6", 1.69),
        ],
        "Baked Goods": [
            ("Croissant Vuoti x6", 1.99),
            ("Fette Biscottate Mulino Bianco x40", 1.89),
            ("Grissini Torinesi 250g", 1.39),
            ("Taralli Pugliesi 300g", 2.19),
            ("Crackers Salati Gran Pavesi 250g", 1.49),
        ],
    },
    "Pasta & Rice": {
        "Pasta": [
            ("Spaghetti Barilla N.5 500g", 0.89),
            ("Penne Rigate De Cecco 500g", 1.19),
            ("Fusilli Rummo 500g", 1.29),
            ("Rigatoni Garofalo 500g", 1.39),
            ("Orecchiette Divella 500g", 1.09),
            ("Linguine Voiello 500g", 1.49),
            ("Farfalle Barilla 500g", 0.99),
            ("Spaghettoni Rummo 500g", 1.39),
            ("Paccheri Garofalo 500g", 1.59),
            ("Tortellini Rana Prosciutto Crudo 250g", 2.99),
            ("Ravioli Ricotta e Spinaci Giovanni Rana 250g", 2.79),
        ],
        "Rice": [
            ("Riso Arborio Scotti 1kg", 2.29),
            ("Riso Carnaroli Gallo 1kg", 2.89),
            ("Riso Basmati Tilda 1kg", 2.49),
        ],
    },
    "Meat & Fish": {
        "Fresh Meat": [
            ("Petto di Pollo al kg", 8.99),
            ("Fettine di Vitello al kg", 16.99),
            ("Macinato di Manzo 400g", 4.49),
            ("Salsiccia di Suino 400g", 3.99),
            ("Cosce di Pollo al kg", 5.49),
            ("Braciole di Maiale al kg", 7.99),
            ("Hamburger di Scottona 2x150g", 4.29),
        ],
        "Cured Meats": [
            ("Prosciutto Crudo di Parma DOP 100g", 3.49),
            ("Prosciutto Cotto Alta Qualità 100g", 2.29),
            ("Mortadella Bologna IGP 150g", 1.99),
            ("Salame Napoli 100g", 2.69),
            ("Bresaola della Valtellina IGP 70g", 3.99),
            ("Pancetta Tesa 100g", 2.49),
            ("Speck Alto Adige IGP 100g", 3.29),
        ],
        "Fresh Fish": [
            ("Filetti di Merluzzo 400g", 5.99),
            ("Gamberi Sgusciati 300g", 7.49),
            ("Salmone Affumicato Norvegese 100g", 4.99),
            ("Tonno Fresco a Tranci al kg", 19.99),
        ],
    },
    "Fruits & Vegetables": {
        "Fresh Fruits": [
            ("Mele Golden al kg", 1.99),
            ("Banane al kg", 1.49),
            ("Arance Tarocco al kg", 1.79),
            ("Fragole 250g", 2.49),
            ("Uva Italia al kg", 2.29),
            ("Kiwi al kg", 2.99),
            ("Pere Abate al kg", 2.19),
            ("Limoni Femminello al kg", 1.69),
        ],
        "Fresh Vegetables": [
            ("Pomodori Ciliegino 500g", 1.99),
            ("Insalata Mista Bonduelle 150g", 1.49),
            ("Zucchine al kg", 1.89),
            ("Melanzane al kg", 1.69),
            ("Peperoni Rossi al kg", 2.49),
            ("Patate al kg", 0.99),
            ("Carote al kg", 0.89),
            ("Cipolla Dorata al kg", 1.19),
            ("Funghi Champignon 400g", 1.79),
            ("Broccoli al kg", 1.99),
        ],
    },
    "Canned & Preserved": {
        "Canned Goods": [
            ("Pomodori Pelati Mutti 400g", 1.09),
            ("Polpa di Pomodoro Cirio 400g", 0.99),
            ("Tonno Rio Mare all'Olio d'Oliva 3x80g", 3.99),
            ("Fagioli Borlotti De Rica 400g", 0.89),
            ("Ceci Valfrutta 400g", 0.79),
            ("Mais Dolce Bonduelle 340g", 1.19),
            ("Passata Rustichella Mutti 700g", 1.49),
        ],
        "Oils & Condiments": [
            ("Olio Extra Vergine di Oliva 1L", 6.99),
            ("Olio EVO Monini Classico 75cl", 5.99),
            ("Aceto Balsamico di Modena IGP 250ml", 2.99),
            ("Pesto alla Genovese Barilla 190g", 2.19),
            ("Salsa di Pomodoro Basilico Barilla 400g", 1.69),
        ],
    },
    "Snacks & Sweets": {
        "Snacks": [
            ("Patatine Classiche San Carlo 150g", 1.99),
            ("Patatine Amica Chips 200g", 1.79),
            ("Fonzies 100g", 1.49),
            ("Schiacciatine Forno Bonomi 250g", 1.89),
            ("Olive Verdi Snocciolate 300g", 2.19),
        ],
        "Sweets & Chocolate": [
            ("Nutella 400g", 3.49),
            ("Biscotti Mulino Bianco Macine 350g", 1.89),
            ("Pan di Stelle 350g", 2.29),
            ("Gocciole Pavesi 500g", 2.49),
            ("Kinder Bueno x3", 1.79),
            ("Ferrero Rocher T16", 5.99),
            ("Cioccolato Fondente Lindt 70% 100g", 2.49),
            ("Ringo Vaniglia x6", 1.69),
        ],
        "Ice Cream": [
            ("Magnum Classic x4", 3.99),
            ("Cornetto Algida Classico x4", 3.49),
            ("Coppa del Nonno x4", 3.29),
        ],
    },
    "Household & Personal Care": {
        "Cleaning Products": [
            ("Detersivo Piatti Fairy 650ml", 1.99),
            ("Detersivo Lavatrice Dash Pods x16", 5.99),
            ("Ammorbidente Coccolino 750ml", 2.49),
            ("Sgrassatore Chanteclair 625ml", 2.29),
            ("Candeggina ACE 1L", 1.49),
            ("Carta Igienica Regina 4 rotoli", 2.19),
        ],
        "Personal Care": [
            ("Shampoo Pantene 225ml", 3.49),
            ("Bagnoschiuma Dove 500ml", 2.99),
            ("Dentifricio Colgate Total 75ml", 2.49),
            ("Deodorante Dove Roll-On 50ml", 2.79),
            ("Sapone Liquido Mani Palmolive 300ml", 1.69),
        ],
    },
}

# Placeholder image base URL (using picsum for generic food images)
IMAGE_BASE = "https://via.placeholder.com/300x300.png?text="


def get_or_create(session, model, defaults=None, **kwargs):
    """Get existing record or create a new one. Returns (instance, created)."""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    instance = model(**kwargs, **(defaults or {}))
    session.add(instance)
    session.flush()
    return instance, True


def generate_price_variation(base_price: float) -> float:
    """Generate a realistic price variation (±15%) rounded to x.x9 or x.x5."""
    variation = random.uniform(-0.15, 0.15)
    price = base_price * (1 + variation)
    # Round to nearest .X9 or .X5 for realism
    cents = random.choice([0.09, 0.19, 0.29, 0.39, 0.49, 0.59, 0.69, 0.79, 0.89, 0.99])
    price = int(price) + cents
    return max(0.19, round(price, 2))


def seed():
    """Populate the database with realistic data."""
    app = create_app(os.getenv("FLASK_ENV", "development"))

    with app.app_context():
        print("🌱 Seeding database...")

        # Stores
        stores = {}
        for name in STORES:
            store, created = get_or_create(db.session, Store, name=name)
            stores[name] = store
            if created:
                print(f"  + Store: {name}")
        db.session.commit()

        # Locations
        locations = {}
        for loc_data in LOCATIONS:
            location, created = get_or_create(
                db.session, Location, city=loc_data["city"], country=loc_data["country"]
            )
            locations[loc_data["city"]] = location
            if created:
                print(f"  + Location: {loc_data['city']}, {loc_data['country']}")
        db.session.commit()

        # Categories, SubCategories, Products, Prices
        product_count = 0
        price_count = 0

        for cat_name, subcategories in CATALOG.items():
            category, created = get_or_create(db.session, Category, name=cat_name)
            if created:
                print(f"  + Category: {cat_name}")

            for subcat_name, products_list in subcategories.items():
                sub_category, created = get_or_create(
                    db.session, SubCategory,
                    name=subcat_name,
                    category_id=category.category_id,
                )
                if created:
                    print(f"    + SubCategory: {subcat_name}")

                for product_name, base_price in products_list:
                    image_url = IMAGE_BASE + product_name.replace(" ", "+")[:30]

                    product, created = get_or_create(
                        db.session, Product,
                        name=product_name,
                        sub_category_id=sub_category.sub_category_id,
                        defaults={"image_url": image_url},
                    )
                    if created:
                        product_count += 1

                    # Create prices: each store in each location
                    # Not every store carries every product (random ~80% chance)
                    for store_name, store in stores.items():
                        for city, location in locations.items():
                            if random.random() < 0.80:  # 80% availability
                                price = generate_price_variation(base_price)
                                last_updated = datetime.now(timezone.utc) - timedelta(
                                    days=random.randint(0, 30)
                                )

                                existing = ProductPrice.query.filter_by(
                                    product_id=product.product_id,
                                    store_id=store.store_id,
                                    location_id=location.location_id,
                                ).first()

                                if not existing:
                                    pp = ProductPrice(
                                        product_id=product.product_id,
                                        store_id=store.store_id,
                                        location_id=location.location_id,
                                        price=price,
                                        last_updated=last_updated,
                                    )
                                    db.session.add(pp)
                                    price_count += 1

            db.session.commit()

        print(f"\n✅ Seeding complete!")
        print(f"   Stores:    {len(STORES)}")
        print(f"   Locations: {len(LOCATIONS)}")
        print(f"   Products:  {product_count} new")
        print(f"   Prices:    {price_count} new")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the price_comparison database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables before seeding",
    )
    args = parser.parse_args()

    if args.reset:
        app = create_app(os.getenv("FLASK_ENV", "development"))
        with app.app_context():
            print("⚠️  Dropping all tables...")
            db.drop_all()
            print("🔨 Creating all tables...")
            db.create_all()

    seed()

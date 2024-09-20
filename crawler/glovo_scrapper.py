import requests
from bs4 import BeautifulSoup
import logging
import itertools
import time
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import argparse
import os

# Configure logging
logging.basicConfig(
    filename='glovo_scraper.log',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Correct DATABASE_URI assignment
DATABASE_URI = 'postgresql://postgres:Gokb3rg.@localhost:5432/productdb'
# Alternatively, use environment variable
# DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///products.db')

Base = declarative_base()
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Define the Store model
class Store(Base):
    __tablename__ = 'stores'

    store_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    # Relationships
    prices = relationship('ProductPrice', backref='store')

# Define the Location model
class Location(Base):
    __tablename__ = 'locations'

    location_id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False, default='Italy')
    # Relationships
    prices = relationship('ProductPrice', backref='location')

# Define the Category model
class Category(Base):
    __tablename__ = 'categories'

    category_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    # Relationships
    sub_categories = relationship('SubCategory', backref='category')

# Define the SubCategory model
class SubCategory(Base):
    __tablename__ = 'sub_categories'

    sub_category_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.category_id'))
    name = Column(String, nullable=False)
    # Relationships
    products = relationship('Product', backref='sub_category')

    __table_args__ = (
        UniqueConstraint('name', 'category_id', name='_sub_category_uc'),
    )

# Define the Product model
class Product(Base):
    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True)
    sub_category_id = Column(Integer, ForeignKey('sub_categories.sub_category_id'))
    name = Column(String, nullable=False)
    link = Column(String)
    image_url = Column(String)
    # Relationships
    prices = relationship('ProductPrice', backref='product')

    __table_args__ = (
        UniqueConstraint('name', 'sub_category_id', name='_product_uc'),
    )

# Define the ProductPrice model
class ProductPrice(Base):
    __tablename__ = 'product_prices'

    price_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id'))
    store_id = Column(Integer, ForeignKey('stores.store_id'))
    location_id = Column(Integer, ForeignKey('locations.location_id'))
    price = Column(Float, nullable=False)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('product_id', 'store_id', 'location_id', name='_price_uc'),
    )

# Base metadata creation
Base.metadata.create_all(engine)

# Configure logging
logging.basicConfig(
    filename='glovo_scraper.log',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_URL = 'https://glovoapp.com'

# Define the mapping of Main Categories to Subcategories
# Define the mapping of Main Categories to Subcategories
category_mapping = {
    "Beverages": {
        "Alcoholic Beverages": [
            "Alcoliche",
            "Alcolici",
            "Aperitivi alcolici",
            "Aperitivi analcolici",
            "Birra in bottiglia",
            "Birra in lattina",
            "Birre",
            "Birre analcoliche",
            "Gin",
            "Limoncello",
            "Liquori",
            "Prosecco",
            "Prosecco e spumante",
            "Rhum",
            "Tequila",
            "Vini bianchi",
            "Vini bianchi DOCG",
            "Vini rossi",
            "Vini rosati e frizzanti",
            "Vino bianco",
            "Vino rosato",
            "Vino rosso",
            "Vodka",
            "Whiskey",
            "Superalcolici"
        ],
        "Non-Alcoholic Beverages": [
            "100% succo",
            "Analcoliche",
            "Analcolici",
            "Acqua frizzante",
            "Acqua naturale",
            "Acqua tonica",
            "Acque aromatizzate",
            "Aromi",
            "Bevande a base di latte",
            "Bevande da aperitivo",
            "Bevande e integratori",
            "Bevande vegetali",
            "Coca-Cola",
            "Cola",
            "Effervescente naturale",
            "Energy drink",
            "Succo di limone",
            "Succhi",
            "Succhi e spremute fresche",
            "Succhi multipack",
            "The",
            "Tè e caffè",
            "Tè freddo",
            "Tè, tisane e camomille",
            "Sostituti del latte",
            "Sostitutivi del latte"
        ],
        "Specialty Beverages": [
            "Aceto",
            "Aceto e glasse",
            "Aromi e decorazioni pasticceria",
            "Aromi e spezie",
            "Caffè in capsule A Modo Mio",
            "Caffè in capsule Dolce Gusto",
            "Caffè in capsule Nespresso",
            "Caffè in cialde",
            "Caffè in grani e macinato",
            "Caffè macinato",
            "Caffè solubile",
            "Caffè solubile, orzo e sostitutivi",
            "Orzo e sostitutivi caffè"
        ]
    },
    "Food": {
        "Dairy Products": [
            "Burro",
            "Burro e margarina senza lattosio",
            "Latte intero",
            "Latte kefir",
            "Latte scremato e parzialmente scremato",
            "Latte scremato e parzialmente scremato senza lattosio",
            "Latte uht intero",
            "Latte uht scremato e parzialmente scremato",
            "Latticini e albumi",
            "Panna fresca",
            "Panna uht",
            "Ricotta",
            "Ricotta e mascarpone",
            "Mascarpone",
            "Yogurt da bere",
            "Yogurt intero - altri gusti",
            "Yogurt intero - bianco",
            "Yogurt intero - frutta",
            "Yogurt intero senza lattosio",
            "Yogurt magro - altri gusti",
            "Yogurt magro - bianco",
            "Yogurt magro - frutta",
            "Yogurt magro senza lattosio"
        ],
        "Meat & Seafood": [
            "Affettati di pollo e tacchino",
            "Affettati e salumi vegetali",
            "Affumicati di pesce",
            "Bresaola",
            "Carne al naturale surgelata",
            "Carne in scatola",
            "Carne macinata",
            "Carne panata surgelata",
            "Mortadella",
            "Prosciutto cotto",
            "Prosciutto crudo",
            "Salame",
            "Salumi e affettati vegetali",
            "Salumi e formaggi",
            "Salumi interi o tranci",
            "Salumi quadrettati",
            "Tonno al naturale",
            "Tonno sott’olio",
            "Pollo",
            "Tacchino",
            "Suino",
            "Pesce al naturale surgelato",
            "Pesce panelaborato surgelato",
            "Prodotti di pesce elaborati",
            "Specialità di pesce",
            "Specialità ittiche"
        ],
        "Bakery & Bread": [
            "Biscotti da pasticceria",
            "Biscotti frollini",
            "Biscotti gelato",
            "Biscotti integrali e salutistici",
            "Biscotti ripieni",
            "Biscotti secchi",
            "Biscotti senza glutine",
            "Biscotti.",
            "Cornetti e croissant",
            "Fette biscottate",
            "Fette Biscottate, confetture e creme spalmbili",
            "Pane bauletto",
            "Pane confezionato e a fette",
            "Pane confezionato senza glutine",
            "Pane croccante",
            "Pane fresco",
            "Pane grattugiato",
            "Panini",
            "Panini per hamburger e hot dog",
            "Panettone",
            "Pandoro",
            "Piadine",
            "Piadine e specialità",
            "Piadine senza glutine",
            "Tramezzini/Toast"
        ],
        "Pasta & Rice": [
            "Pasta Fresca",
            "Pasta all'uovo",
            "Pasta corta senza glutine",
            "Pasta di semola brodi e minestrine",
            "Pasta di semola corta",
            "Pasta di semola lunga",
            "Pasta di semola specialità",
            "Pasta e riso surgelati",
            "Pasta e sughi",
            "Pasta fresca non ripiena",
            "Pasta fresca ripiena",
            "Pasta integrale, farro e altri",
            "Pasta lunga senza glutine",
            "Pasta ripiena e gnocchi",
            "Pasta sfoglia e altri basi",
            "Paste filate",
            "Riso bianco",
            "Riso parboiled",
            "Riso specialità",
            "Risotto"
        ],
        "Condiments & Sauces": [
            "Condimenti",
            "Condimenti e conserve",
            "Ketchup e barbeque",
            "Maionese",
            "Salse lunga conservazione",
            "Salse, patè e spalmabili",
            "Sughi",
            "Sughi a lunga conservazione",
            "Sughi e salse surgelati",
            "Sughi freschi",
            "Sughi pronti",
            "Passata di pomodoro",
            "Polpa di pomodoro",
            "Concentrati di pomodoro",
            "Concentrato di pomodoro"
        ],
        "Snacks": [
            "Barrette dolci",
            "Barrette e Merendine",
            "Barrette e altri prodotti dietetici",
            "Barrette senza glutine",
            "Crackers",
            "Crackers, gallette e grissini senza glutine",
            "Gallette",
            "Merendine",
            "Merendine senza glutine",
            "Snack cioccolato",
            "Snack dolci",
            "Snack dolci e salati",
            "Snack salati",
            "Snacks salati",
            "Pop corn",
            "Taralli",
            "Taralli, patatine e stuzzichini",
            "Tavolette di cioccolato",
            "Wafer",
            "Wafers"
        ],
        "Frozen Foods": [
            "Carne al naturale surgelata",
            "Carne panata surgelata",
            "Pizza condita surgelata",
            "Pizza margherita surgelata",
            "Panetteria surgelata",
            "Pasticceria surgelata",
            "Pesce al naturale surgelato",
            "Pesce panelaborato surgelato",
            "Minestroni e vellutate surgelate",
            "Patatine surgelate",
            "Secondi vegetali surgelati",
            "Preparati di pesce surgelati",
            "Surgelati",
            "Surgelati e gelati",
            "Pizze e focacce",
            "Pizzeria",
            "Sorbetti",
            "Stecchi gelato",
            "Torte gelato"
        ],
        "Fresh Produce": [
            "Altra frutta fresca",
            "Altra verdura fresca",
            "Altre alternative vegetali",
            "Altri prodotti vegetali",
            "Carote",
            "Mele",
            "Pere",
            "Sedano",
            "Zucchine, melanzane e peperoni",
            "Funghi",
            "Funghi conservati",
            "Fragole e frutti di bosco",
            "Frutta esotica",
            "Frutta essiccata e disidratata",
            "Frutta preparata",
            "Frutta sciroppata",
            "Frutta secca con guscio",
            "Frutta secca senza guscio",
            "Piante aromatiche"
        ],
        "Specialty & Gourmet": {
            "Specialty Foods": [
                "Altra pasta speciale",
                "Altre conserve di pesce",
                "Altre salse a lunga conservazione",
                "Altre specialità di riso",
                "Altri prodotti vegetali",
                "Specialità vegetali",
                "Specialità ittiche"
            ],
            "Gourmet Items": [
                "Grana",
                "Grappa",
                "Marmellate",
                "Miele",
                "Olio extravergine d'oliva",
                "Olio d’oliva",
                "Olio extravergine d’oliva",
                "Olive",
                "Olive e frutta secca"
            ]
        }
    },
    "Personal Care": {
        "Hair Care": [
            "Accessori capelli",
            "Balsamo capelli",
            "Colorazione capelli",
            "Shampoo",
            "Shampoo + balsamo",
            "Shampoo capelli",
            "Shampoo e balsamo",
            "Maschere e trattamento capelli",
            "Styling capelli"
        ],
        "Skin & Body Care": [
            "Accessori e altro cura corpo",
            "Bagno doccia schiuma",
            "Bagno e doccia schiuma",
            "Bagno/Doccia",
            "Balsamo e maschere",
            "Creme corpo e talco",
            "Creme e gel mani",
            "Creme spalmabili",
            "Cura viso e creme",
            "Corpo",
            "Cosmetica unghie",
            "Cosmetica viso",
            "Maschere e altro cura viso",
            "Tinte"
        ],
        "Oral Care": [
            "Accessori pulizia denti",
            "Dentifrici",
            "Spazzolini"
        ],
        "Deodorants & Antiperspirants": [
            "Deodorante roll-on",
            "Deodorante spray",
            "Deodoranti",
            "Deodoranti azione continua",
            "Deodoranti azione istantanea",
            "Deodoranti roll-on",
            "Deodoranti spray"
        ],
        "Other Personal Care": [
            "Depilazione donna",
            "Profumi persona",
            "Pre/Post barba",
            "Prodotti dopo barba",
            "Prodotti pre barba",
            "Rasoi uomo",
            "Lame e rasoi donna",
            "Lame e rasoi uomo",
            "Intimo",
            "Intimo donna"
        ]
    },
    "Household Products": {
        "Cleaning Supplies": [
            "Additivi lavastoviglie",
            "Candeggina",
            "Candeggine e detergenti bagno",
            "Detergenti multiuso",
            "Detergenti per pavimenti",
            "Detergenti superfici",
            "Detergenti e salviette intime",
            "Detergenti e struccanti",
            "Detergenti intimi",
            "Insetticidi striscianti",
            "Insetticidi volanti",
            "Lavastoviglie",
            "Lavastoviglie in caps",
            "Lavastoviglie liquido e in polvere",
            "Lavatrice",
            "Anticalcare",
            "Anticalcare e addittivi lavatrice",
            "Igienizzanti, sgrassatori e anticalcare",
            "Trattamento superfici e mobilio"
        ],
        "Laundry Supplies": [
            "Ammorbidenti",
            "Ammorbidenti e profumatori",
            "Detersivi lavatrice liquidi e in caps",
            "Saponi bucato",
            "Trattamento bucato/asciugatura"
        ],
        "Paper Products": [
            "Carta igienica",
            "Rotoli di carta",
            "Rotoli e tovaglioli di carta",
            "Tovaglioli",
            "Fazzoletti",
            "Fazzolettini",
            "Panni e spugne"
        ],
        "Kitchen Supplies": [
            "Alluminio, pellicola e carta forno",
            "Avvolgenti per alimenti",
            "Sacchetti e vaschette per alimenti",
            "Sacchetti/Vaschette",
            "Vaschette",
            "Vaschette gelato",
            "Sacchetti per la spazzatura",
            "Utensileria cucina",
            "Pentole, padelle e teglie",
            "Stoviglie",
            "Piatti, bicchieri e posate"
        ],
        "Laundry Supplies": [
            "Ammorbidenti",
            "Ammorbidenti e profumatori",
            "Detersivi lavatrice liquidi e in caps",
            "Saponi bucato",
            "Trattamento bucato/asciugatura"
        ],
        "Miscellaneous Household Items": [
            "Articoli sanitari",
            "Bastoncini di cotone",
            "Bastoncini e cotone",
            "Candele profumate",
            "Candeline torta",
            "Candeline torte",
            "Guanti",
            "Nidi",
            "Stendo e stiro"
        ]
    },
    "Pet Supplies": {
        "Dog Supplies": [
            "Cibo secco e crocchette cane",
            "Cibo umido cane",
            "Snack e biscotti cane",
            "Igiene e accessori cane"
        ],
        "Cat Supplies": [
            "Cibo secco e crocchette gatto",
            "Cibo umido gatto",
            "Snack gatto",
            "Igiene e accessori gatto"
        ],
        "Other Pets": [
            "Cibo altri animali"
        ]
    },
    "Health & Wellness": {
        "Medical Supplies": [
            "Articoli sanitari",
            "Pronto soccorso"
        ],
        "Personal Health": [
            "Incontinenza",
            "Cura delle dentiere",
            "Integratori alimentari",
            "Integratori e vitamine",
            "Assorbenti esterni",
            "Assorbenti interni",
            "Protezioni solari"
        ],
        "Health Care Products": [
            "Cura viso e creme",
            "Cura wc e tubature",
            "Prodotti proteici"
        ]
    },
    "Household Accessories": {
        "Storage & Organization": [
            "Borse e shopper riutilizzabili",
            "Shopper"
        ],
        "Home Decor": [
            "Candele profumate",
            "Candeline torta",
            "Candeline torte",
            "Lucidi e cura scarpe"
        ],
        "Miscellaneous Accessories": [
            "Accessori cibo",
            "Accessori",
            "Accessori pulizia denti"
        ]
    },
    "Specialty & Gourmet": {
        "Specialty Foods": [
            "Altra pasta speciale",
            "Altre conserve di pesce",
            "Altre salse a lunga conservazione",
            "Altre specialità di riso",
            "Altri prodotti vegetali",
            "Specialità vegetali",
            "Specialità ittiche"
        ],
        "Gourmet Items": [
            "Grana",
            "Grappa",
            "Marmellate",
            "Miele",
            "Olio extravergine d'oliva",
            "Olio d’oliva",
            "Olio extravergine d’oliva",
            "Olive",
            "Olive e frutta secca"
        ]
    },
    "Frozen & Refrigerated": {
        "Frozen Meals": [
            "Piatti pronti",
            "Secondi piatti pronti",
            "Insalate",
            "Minestroni e vellutate surgelate"
        ],
        "Frozen Desserts": [
            "Dessert gelato",
            "Torte gelato"
        ],
        "Frozen Ingredients": [
            "Preparati di pesce surgelati",
            "Preparati per bevande"
        ]
    },
    "Snacks & Sweets": {
        "Sweet Snacks": [
            "Barrette dolci",
            "Barrette e Merendine",
            "Barrette e altri prodotti dietetici",
            "Barrette senza glutine",
            "Caramelle",
            "Caramelle dure",
            "Caramelle morbide",
            "Tavolette di cioccolato",
            "Praline e cioccolatini",
            "Torrone",
            "Wafer",
            "Wafers"
        ],
        "Savory Snacks": [
            "Snack salati",
            "Snacks salati",
            "Patatine",
            "Taralli, patatine e stuzzichini"
        ]
    },
    "Miscellaneous": {
        "Cooking Essentials": [
            "Farina",
            "Farine e altre miscele",
            "Semi",
            "Lieviti",
            "Olio d'oliva",
            "Olio di semi"
        ],
        "Specialty Ingredients": [
            "Aromi e spezie",
            "Aromi",
            "Spezie ed aromi"
        ],
        "Others": [
            "Utensileria cucina",
            "Prodotti pre barba",
            "Prodotti dopo barba",
            "Prodotti proteici",
            "Prodotti per la salute",
            "Prodotti per pavimenti"
        ]
    }
}

# Utility functions to interact with the category mapping

def find_main_category(subcategory_name):
    """Find and return the main category and subcategory for a given subcategory name."""
    for main_category, subcategories in category_mapping.items():
        if isinstance(subcategories, dict):
            for subcat_key, subcat_list in subcategories.items():
                if subcategory_name in subcat_list:
                    return main_category, subcat_key
        else:
            if subcategory_name in subcategories:
                return main_category, None
    return "Uncategorized", "Uncategorized"

def extract_subcategory_links(soup):
    links = []
    # Update the selectors based on the current website structure
    carousel_elements = soup.find_all('div', {'class': 'carousel__content__element'})

    for element in carousel_elements:
        a_tag = element.find('a', href=True)
        if a_tag:
            link = a_tag['href']
            if not link.startswith('http'):
                link = BASE_URL + link 
            links.append(link)
    return links

def scrape_product_details(link):
    try:
        time.sleep(2)  # Throttle requests
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                ' AppleWebKit/537.36 (KHTML, like Gecko)'
                ' Chrome/85.0.4183.102 Safari/537.36'
            )
        }
        response = requests.get(link, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        all_products = []
        grids = soup.find_all('div', class_='grid')

        for grid in grids:
            sub_category_name = grid.find('h2', class_='grid__title').get_text(strip=True) if grid.find('h2', class_='grid__title') else 'N/A'
        
            category_name, sub_category_key = find_main_category(sub_category_name)
            for item in grid.find_all('div', class_='tile'):
                product_name = item.find('span', class_='tile__description').get_text(strip=True) if item.find('span', class_='tile__description') else 'N/A'
                
                # Extract and clean the price
                product_price = item.find('span', class_='product-price__effective').get_text(strip=True) if item.find('span', 'product-price__effective') else 'N/A'
                if product_price != 'N/A':
                    product_price = product_price.replace('€', '').replace(',', '.').strip()  # Remove the Euro symbol and replace comma with dot
                    try:
                        product_price = float(product_price)  # Convert to float
                    except ValueError:
                        logging.error(f"Error converting price '{product_price}' to float.")
                        product_price = None  # Assign None if conversion fails
                
                image_url = item.find('img', class_='tile__image')['src'] if item.find('img', class_='tile__image') else 'N/A'

                all_products.append({
                    'link': link,
                    'sub_category': sub_category_name,
                    'category': category_name,
                    'name': product_name,
                    'price': product_price,
                    'image_url': image_url
                })
        return all_products

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {link}: {e}")
        return []
def upsert_product(session, product_data, store_name, location_name):
    try:
         # Get or create Store
        store = session.query(Store).filter_by(name=store_name).first()
        if not store:
            store = Store(name=store_name)
            print(store)
            session.add(store)
            session.commit()

        # Get or create Location
        location = session.query(Location).filter_by(city=location_name).first()
        if not location:
            location = Location(city=location_name)
            session.add(location)
            session.commit()

        # Get or create Category
        category = session.query(Category).filter_by(name=product_data['category']).first()
        if not category:
            category = Category(name=product_data['category'])
            session.add(category)
            session.commit()

        # Get or create SubCategory
        sub_category = session.query(SubCategory).filter_by(
            name=product_data['sub_category'],
            category_id=category.category_id
        ).first()
        if not sub_category:
            sub_category = SubCategory(name=product_data['sub_category'], category=category)
            session.add(sub_category)
            session.commit()

        # Get or create Product
        product = session.query(Product).filter_by(
            name=product_data['name'],
            sub_category_id=sub_category.sub_category_id
        ).first()
        if not product:
            product = Product(
                name=product_data['name'],
                sub_category=sub_category,
                link=product_data['link'],
                image_url=product_data['image_url']
            )
            session.add(product)
            session.commit()
        else:
            # Update existing product details if necessary
            product.link = product_data['link']
            product.image_url = product_data['image_url']
            session.commit()

        # Insert or update ProductPrice
        product_price = session.query(ProductPrice).filter_by(
            product_id=product.product_id,
            store_id=store.store_id,
            location_id=location.location_id
        ).first()

        if not product_price:
            # Insert new price entry
            product_price = ProductPrice(
                product=product,
                store=store,
                location=location,
                price=product_data['price'],
                last_updated=datetime.utcnow()
            )
            session.add(product_price)
        else:
            # Update existing price if it has changed
            if product_price.price != product_data['price']:
                product_price.price = product_data['price']
                product_price.last_updated = datetime.utcnow()
        session.commit()

        logging.info(f"Upserted product: {product_data['name']}")
    except Exception as e:
        logging.error(f"Failed to upsert product {product_data['name']}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape product data from Glovo")
    parser.add_argument(
        "--stores",
        nargs="+",
        choices=["penny", "conad", "deco"],
        default=["penny", "conad", "deco"],
        help="Stores to scrape"
    )
    parser.add_argument(
        "--locations",
        nargs="+",
        choices=["roma"],
        default=["roma"],
        help="Locations to scrape"
    )
    args = parser.parse_args()

    # Iterate through stores and locations
    for store_name, location_name in itertools.product(args.stores, args.locations):
        logging.info(f"Scraping {store_name} in {location_name}")

        # Update the URL format based on the actual Glovo URL structure
        url = f"{BASE_URL}/it/it/{location_name}/{store_name}-{location_name[0:3]}/"

        try:
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                    ' AppleWebKit/537.36 (KHTML, like Gecko)'
                    ' Chrome/85.0.4183.102 Safari/537.36'
                )
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            subcategory_links = extract_subcategory_links(soup)

            for link in subcategory_links:
                logging.info(f"  Scraping subcategory: {link}")
                products = scrape_product_details(link)
                print(f'products:{products}')
                for product in products:
                    print(f'product:{product}')
                    
                    upsert_product(session, product, store_name, location_name)
                logging.info(f"  Data saved for {store_name} in {location_name}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching main page for {store_name} in {location_name}: {e}")

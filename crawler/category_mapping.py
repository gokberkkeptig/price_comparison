"""
Maps Italian subcategory names from Glovo to English category/subcategory pairs.

This mapping allows the crawler to classify scraped products into a normalized
category hierarchy even though Glovo uses Italian labels.
"""

CATEGORY_MAPPING = {
    "Beverages": {
        "Alcoholic Beverages": [
            "Alcoliche", "Alcolici", "Aperitivi alcolici", "Birra in bottiglia",
            "Birra in lattina", "Birre", "Birre analcoliche", "Gin", "Limoncello",
            "Liquori", "Prosecco", "Prosecco e spumante", "Rhum", "Tequila",
            "Vini bianchi", "Vini bianchi DOCG", "Vini rossi",
            "Vini rosati e frizzanti", "Vino bianco", "Vino rosato", "Vino rosso",
            "Vodka", "Whiskey", "Superalcolici",
        ],
        "Non-Alcoholic Beverages": [
            "100% succo", "Analcoliche", "Analcolici", "Acqua frizzante",
            "Acqua naturale", "Acqua tonica", "Acque aromatizzate",
            "Bevande a base di latte", "Bevande da aperitivo",
            "Bevande e integratori", "Bevande vegetali", "Coca-Cola", "Cola",
            "Effervescente naturale", "Energy drink", "Succo di limone", "Succhi",
            "Succhi e spremute fresche", "Succhi multipack", "The", "Thé",
            "Tè freddo", "Tisane",
        ],
    },
    "Dairy & Eggs": {
        "Milk": [
            "Latte", "Latte UHT", "Latte fresco", "Latte vegetale",
            "Panna e besciamella", "Panna",
        ],
        "Cheese": [
            "Formaggi", "Formaggi freschi", "Formaggi stagionati",
            "Mozzarella e burrata", "Ricotta", "Mascarpone",
        ],
        "Yogurt": [
            "Yogurt", "Yogurt bianco", "Yogurt alla frutta",
            "Yogurt greco", "Dessert e budini",
        ],
        "Eggs": ["Uova"],
    },
    "Bread & Bakery": {
        "Bread": [
            "Pane", "Pane fresco", "Pane confezionato", "Panini",
            "Piadine e wraps", "Focacce",
        ],
        "Baked Goods": [
            "Fette biscottate", "Grissini", "Cracker", "Taralli",
            "Croissant", "Brioche", "Merendine",
        ],
    },
    "Pasta & Rice": {
        "Pasta": [
            "Pasta", "Pasta corta", "Pasta lunga", "Pasta fresca",
            "Pasta ripiena", "Pasta integrale", "Gnocchi",
        ],
        "Rice": [
            "Riso", "Riso arborio", "Riso basmati", "Riso carnaroli",
            "Cereali e legumi secchi",
        ],
    },
    "Meat & Fish": {
        "Fresh Meat": [
            "Carne", "Carne bovina", "Carne suina", "Pollo e tacchino",
            "Carne macinata", "Hamburger",
        ],
        "Cured Meats": [
            "Salumi", "Prosciutto", "Prosciutto crudo", "Prosciutto cotto",
            "Salame", "Mortadella", "Bresaola", "Speck", "Pancetta",
            "Affettati",
        ],
        "Fresh Fish": [
            "Pesce", "Pesce fresco", "Pesce surgelato", "Gamberi",
            "Salmone", "Tonno",
        ],
    },
    "Fruits & Vegetables": {
        "Fresh Fruits": [
            "Frutta", "Frutta fresca", "Frutta di stagione", "Frutta esotica",
            "Agrumi",
        ],
        "Fresh Vegetables": [
            "Verdura", "Verdura fresca", "Ortaggi", "Insalate",
            "Insalate pronte", "Pomodori", "Patate", "Funghi",
        ],
    },
    "Canned & Preserved": {
        "Canned Goods": [
            "Conserve", "Pelati e passate", "Legumi in scatola",
            "Tonno in scatola", "Sottoli e sottaceti",
        ],
        "Oils & Condiments": [
            "Olio", "Olio extra vergine", "Olio di oliva", "Olio di semi",
            "Aceto", "Aceto balsamico", "Condimenti", "Sughi e pesti",
            "Sale e pepe", "Spezie ed aromi",
        ],
    },
    "Snacks & Sweets": {
        "Snacks": [
            "Patatine", "Snack salati", "Olive", "Frutta secca",
            "Crackers e grissini",
        ],
        "Sweets & Chocolate": [
            "Cioccolato", "Biscotti", "Dolci", "Caramelle e gomme",
            "Creme spalmabili", "Nutella", "Marmellate e miele",
        ],
        "Ice Cream": [
            "Gelati", "Gelato", "Ghiaccioli", "Gelati confezionati",
        ],
    },
    "Household & Personal Care": {
        "Cleaning Products": [
            "Detersivi", "Detersivo piatti", "Detersivo lavatrice",
            "Ammorbidente", "Sgrassatore", "Candeggina",
            "Carta igienica", "Carta casa",
            "Prodotti per pavimenti",
        ],
        "Personal Care": [
            "Bagnoschiuma", "Shampoo", "Sapone", "Dentifricio",
            "Deodorante", "Prodotti pre barba", "Prodotti dopo barba",
            "Igiene orale", "Igiene personale",
        ],
    },
}


def find_category(subcategory_name: str) -> tuple[str, str]:
    """
    Find the English (category, subcategory) pair for an Italian subcategory name.

    Returns ("Uncategorized", "Uncategorized") if no match is found.
    """
    for main_category, subcategories in CATEGORY_MAPPING.items():
        for sub_key, italian_names in subcategories.items():
            if subcategory_name in italian_names:
                return main_category, sub_key
    return "Uncategorized", "Uncategorized"

import sqlite3
from app import app
from app import db
from app.models import Product

def import_data():
    # Connect to the existing products.db
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    # Fetch all data from the existing products table
    cursor.execute("SELECT id, name, price, image_url FROM products")
    products = cursor.fetchall()

    # Insert data into the new database
    for product in products:
        new_product = Product(id=product[0], name=product[1], price=product[2], image_url=product[3])
        db.session.add(new_product)

    db.session.commit()
    conn.close()

if __name__ == '__main__':
    import_data()
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db
from app.models import Product, ProductPrice, Store, Location, Category, SubCategory, User
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import joinedload
from flask import request, render_template
from PIL import Image
import io, re
import base64
import pytesseract
from langchain_ollama import OllamaLLM
import json

pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\ygkep\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'
tessdata_dir_config = "C:\\Users\\ygkep\\AppData\\Local\\Programs\\Tesseract-OCR\\tessdata"
# Aggiungi l'opzione -l per indicare che la lingua è l'italiano
config = f'{tessdata_dir_config}\\ita.traineddata'


@app.route('/', methods=['GET'])
def home():
    # Retrieve parameters with defaults
    query = request.args.get('query', '').strip()
    order_by = request.args.get('order_by', 'asc').strip()
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    per_page = 20  # Items per page
    category_filter = request.args.get('category', '').strip()
    store_filter = request.args.get('store', '').strip()
    city_filter = request.args.get('city', '').strip()

    # Base query
    products_query = Product.query

    # Join necessary tables to enable filtering and searching
    products_query = products_query.join(ProductPrice).join(Store).join(SubCategory).join(Category).join(Location)

    # Eager load related data to optimize performance
    products_query = products_query.options(
        joinedload(Product.sub_category).joinedload(SubCategory.category),
        joinedload(Product.prices).joinedload(ProductPrice.store),
        joinedload(Product.prices).joinedload(ProductPrice.location)
    )

    # Apply city filter first
    if city_filter:
        products_query = products_query.filter(Location.city.ilike(city_filter))

    # Apply full-text search if query is provided
    if query:
        # Create a full-text search vector
        search_vector = func.to_tsvector('english', func.concat_ws(' ', Product.name, SubCategory.name, Category.name))
        # Create a search query
        search_query = func.plainto_tsquery('english', query)
        # Filter products matching the search query
        products_query = products_query.filter(search_vector.op('@@')(search_query))

    # Apply category filter if selected
    if category_filter:
        products_query = products_query.filter(Category.name.ilike(category_filter))

    # Apply store filter if selected
    if store_filter:
        products_query = products_query.filter(Store.name.ilike(store_filter))

    # Aggregate to get the minimum price per product
    products_query = products_query.add_columns(func.min(ProductPrice.price).label('min_price'))

    # Group by product to handle aggregation
    products_query = products_query.group_by(Product.product_id)

    # Apply ordering based on price
    if order_by == 'desc':
        products_query = products_query.order_by(desc('min_price'))
    else:
        products_query = products_query.order_by(asc('min_price'))

    # Paginate the results
    products_pagination = products_query.paginate(page=page, per_page=per_page, error_out=False)

    # Retrieve distinct categories, stores, and cities for the dropdowns
    categories = Category.query.order_by(Category.name.asc()).all()
    stores = Store.query.order_by(Store.name.asc()).all()
    cities = Location.query.order_by(Location.city.asc()).all()

    return render_template('index.html', 
                           products=products_pagination.items, 
                           categories=categories, 
                           stores=stores,
                           cities=cities,
                           order_by=order_by, 
                           selected_category=category_filter, 
                           selected_store=store_filter, 
                           selected_city=city_filter, 
                           page=page,
                           total_pages=products_pagination.pages,
                           query=query)
from flask import render_template, request, redirect, url_for, flash
@app.route('/compare', methods=['GET'])
def compare():
    product_ids = request.args.getlist('compare_products')
    if not product_ids:
        flash('No products selected for comparison.', 'warning')
        return redirect(url_for('home'))

    # Limit the number of products to compare (e.g., max 4)
    if len(product_ids) > 4:
        flash('You can compare up to 4 products at a time.', 'warning')
        return redirect(url_for('home'))

    # Fetch the products and related data
    products = Product.query.options(
        joinedload(Product.sub_category).joinedload(SubCategory.category),
        joinedload(Product.prices).joinedload(ProductPrice.store),
        joinedload(Product.prices).joinedload(ProductPrice.location)
    ).filter(Product.product_id.in_(product_ids)).all()

    # Identify the cheapest product
    product_prices = {}
    for product in products:
        min_price = min([price.price for price in product.prices])
        product_prices[product.product_id] = min_price

    # Find the product ID with the lowest price
    cheapest_product_id = min(product_prices, key=product_prices.get)

    return render_template('compare.html', products=products, cheapest_product_id=cheapest_product_id)

# Route to display a single product's details
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.options(
        joinedload(Product.sub_category).joinedload(SubCategory.category),
        joinedload(Product.prices).joinedload(ProductPrice.store),
        joinedload(Product.prices).joinedload(ProductPrice.location)
    ).get_or_404(product_id)
    return render_template('product_detail.html', product=product)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username già in uso. Scegline un altro.', 'error')
            return render_template('register.html')

       

        new_user = User(username=username, password=password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registrazione completata! Puoi effettuare il login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()  # In caso di errore, annulla la sessione
            flash('Si è verificato un errore durante la registrazione. Riprova.', 'danger')
            print(f"Errore: {e}")  # Stampa l'errore nel terminale

    return render_template('register.html')  # Restituisci il template per la registrazione


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

    
        user = User.query.filter_by(username=username).first()

        # Verifica la password
        if not user or not (user.password, password):
            flash('Credenziali non valide. Riprova.', 'danger')
            return redirect(url_for('login'))

        # Autenticazione riuscita, salva l'utente nella sessione
        session['user_id'] = user.id
        session['username'] = user.username

        flash('Accesso eseguito con successo', 'success')
        return redirect(url_for('home'))

    return render_template('login.html')


# Route per il logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logout effettuato con successo', 'success')
    return redirect(url_for('home'))



# Route per reindirizzare alla telecamera
@app.route('/camera_access')
def camera_access():
    # Qui puoi aggiungere la logica per accedere alla telecamera
    # In questo esempio ti reindirizzo semplicemente ad una nuova pagina
    return render_template('camera_access.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    image_data = data['image']
    
    # Remove the header of the base64 string
    image_data = re.sub('^data:image/.+;base64,', '', image_data)
    
    # Decode the base64 string
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes))
    
    # Perform OCR on the image
    extracted_text = pytesseract.image_to_string(image, lang='ita', config=config)
    print(extracted_text)
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
        "3. If you cannot find some of the required information, leave that field empty in the JSON result.\n"
        "4. Provide the result in JSON format, with the keys 'store_name', 'date', and 'items'.\n"
        "5. The 'items' key should be a list of objects, each with the keys 'name' and 'price'.\n"
        "6. The 'price' should be a decimal number, using a dot as the decimal separator (e.g., 4.99).\n"
        "7. When the store name is unclear or missing,make sure that you use famous supermarkets in Italy as the 'store_name' (e.g., CONAD, PENNY).\n"
        "8. Make sure that use dateformat as 'dd/mm/yyyy'.\n"
        "9. Example output:\n"
        "{\n"
        '  "store_name": "CONAD",\n'
        '  "date": "09/09/2024",\n'
        '  "items": [\n'
        '    {"name": "BIRBE RINGS AMADORI", "price": 4.99},\n'
        '    {"name": "PANE INTEGRALE", "price": 2.50}\n'
        '  ]\n'
        '}\n'
    )

    model = OllamaLLM(model='llama3.2')  
    print(prompt)

    response = model.invoke(input=prompt)
    print(response)
    import datetime
    
    feedback_messages = []
    
    # Parse the JSON response
    try:
        receipt_data = json.loads(response)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return jsonify({'error': 'Invalid response format'}), 400
    
    # Now, process the receipt_data and insert/update the database accordingly
    print(receipt_data)
    # Handle the store
    store_name = receipt_data.get('store_name', '').strip()
    store_name = store_name.lower()  # Convert to lowercase for consistency
    if not store_name:
        store_name = 'Unknown Store'  # Default value or handle as per your requirement
    store = Store.query.filter_by(name=store_name).first()
    if not store:
        store = Store(name=store_name)
        db.session.add(store)
        db.session.flush()  # To get the store_id
    
    # Handle the receipt date
    receipt_date_str = receipt_data.get('date', '').strip()
    try:
        receipt_date = datetime.datetime.strptime(receipt_date_str, '%d/%m/%Y') 

    except ValueError:
        receipt_date = datetime.utcnow()  # Default to current date or handle as per your requirement
    
    # Ensure there is an 'Uncategorized' category and subcategory
    category = Category.query.filter_by(name='Uncategorized').first()
    if not category:
        category = Category(name='Uncategorized')
        db.session.add(category)
        db.session.flush()  # To get category_id

    sub_category = SubCategory.query.filter_by(name='Uncategorized', category_id=category.category_id).first()
    if not sub_category:
        sub_category = SubCategory(name='Uncategorized', category_id=category.category_id)
        db.session.add(sub_category)
        db.session.flush()  # To get sub_category_id

    # Ensure there is a default location
    location = Location.query.filter_by(city='Napoli', country='Italy').first()
    if not location:
        location = Location(city='Napoli', country='Italy')
        db.session.add(location)
        db.session.flush()  # To get location_id

    # Handle the items
    items = receipt_data.get('items', [])
    for item in items:
        product_name = item.get('name', '').strip()
        product_name = product_name.title()  # Convert to title for consistency
        price_str = item.get('price')
        
        # Convert price to float
        try:
            if price_str is None:
                raise ValueError("Price is missing")
            elif isinstance(price_str, (float, int)):
                price = float(price_str)
            elif isinstance(price_str, str):
                price_str_converted = price_str.replace(',', '.')
                price = float(price_str_converted)
            else:
                raise ValueError(f"Unexpected type for price_str: {type(price_str)}")
        except Exception as e:
            feedback_messages.append(f"Invalid price '{price_str}' for item '{product_name}': {e}")
            continue

        # Check if the product exists
        product = Product.query.filter_by(name=product_name).first()
        print(product)
        if product:
            # Product exists
            # Check if there is a ProductPrice for this product, store, and location
            product_price = ProductPrice.query.filter_by(
                product_id=product.product_id,
                
                store_id=store.store_id,
                location_id=location.location_id
            ).first()
            print(product.product_id)
            if product_price:
                # Compare last_updated dates
                if product_price.last_updated < receipt_date:
                    # Update price and last_updated
                    if product_price.price != price:
                        product_price.price = price
                        feedback_messages.append(f"Price updated to '{price}' for product '{product_name}'")
                    product_price.last_updated = receipt_date
                    db.session.add(product_price)
                else:
                    # The existing price is more recent, do nothing
                    feedback_messages.append(f"Price '{price}' for product '{product_name}' is older than the existing price")
                    pass
            else:
                # No existing ProductPrice, create a new one
                product_price = ProductPrice(
                    product_id=product.product_id,
                    store_id=store.store_id,
                    location_id=location.location_id,
                    price=price,
                    last_updated=receipt_date
                )
                db.session.add(product_price)
                feedback_messages.append(f"New price '{price}' added for product '{product_name}'")
        else:
            # Product does not exist, create a new one
            product = Product(
                name=product_name,
                sub_category_id=sub_category.sub_category_id,
                image_url='https://glovoapp.com/images/svg/product/general.svg'
                # link can be None
            )
            db.session.add(product)
            db.session.flush()  # To get product_id
            
            # Create a new ProductPrice entry
            product_price = ProductPrice(
                product_id=product.product_id,
                store_id=store.store_id,
                location_id=location.location_id,
                price=price,
                last_updated=receipt_date
            )
            db.session.add(product_price)
            feedback_messages.append(f"New product '{product_name}' added to the database")
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Data inserted/updated successfully',
            'feedback': feedback_messages
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error inserting/updating the database: {e}")
        return jsonify({'error': 'Database operation failed'}), 500
    
    
    
@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/get_cart_products', methods=['POST'])
def get_cart_products():
    data = request.get_json()
    cart = data.get('cart', {})
    product_ids = cart.keys()

    # Fetch products from the database
    products = Product.query.filter(Product.product_id.in_(product_ids)).all()

    # Serialize products and their prices
    products_data = []
    for product in products:
        product_info = {
            'product_id': product.product_id,
            'name': product.name,
            'prices': [],
            'image_url': product.image_url
        }
        for price in product.prices:
            product_info['prices'].append({
                'store': price.store.name,
                'price': price.price
            })
        products_data.append(product_info)

    # Get a list of all stores
    stores = Store.query.all()
    store_names = [store.name for store in stores]

    return jsonify({'products': products_data, 'stores': store_names})

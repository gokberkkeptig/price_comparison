from flask import render_template, request, redirect, url_for, flash
from app import app, db
from app.models import Product, ProductPrice, Store, Location, Category, SubCategory
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import joinedload
from flask import request, render_template
from sqlalchemy.orm import joinedload
from sqlalchemy import func, desc, asc

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

    # Base query
    products_query = Product.query

    # Join necessary tables to enable filtering and searching
    products_query = products_query.join(ProductPrice).join(Store).join(SubCategory).join(Category)

    # Eager load related data to optimize performance
    products_query = products_query.options(
        joinedload(Product.sub_category).joinedload(SubCategory.category),
        joinedload(Product.prices).joinedload(ProductPrice.store),
        joinedload(Product.prices).joinedload(ProductPrice.location)
    )

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

    # Retrieve distinct categories and stores for the dropdowns
    categories = Category.query.order_by(Category.name.asc()).all()
    stores = Store.query.order_by(Store.name.asc()).all()
    subcategories = SubCategory.query.order_by(SubCategory.name.asc()).all()

    return render_template('index.html', 
                           products=products_pagination.items, 
                           categories=categories, 
                           SubCategory=subcategories,
                           stores=stores,
                           order_by=order_by, 
                           selected_category=category_filter, 
                           selected_store=store_filter, 
                           page=page,
                           total_pages=products_pagination.pages,
                           query=query)  # Pass the query to the template
    
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

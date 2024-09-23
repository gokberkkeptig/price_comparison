from flask import render_template, request, redirect, url_for, flash
from app import app
from app.models import Product, ProductPrice, Store, Location, Category, SubCategory
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import joinedload

@app.route('/', methods=['GET'])
def home():
    query = request.args.get('query', '')  # Default to empty string if no search
    order_by = request.args.get('order_by', 'asc')  # Default to ascending order
    page = int(request.args.get('page', 1))  # Default to page 1
    per_page = 20  # Items per page
    category_filter = request.args.get('category', '')  # Default to empty string for category filter
    store_filter = request.args.get('store', '')  # Default to empty string for store filter

    # Base query
    products_query = Product.query

    # Join necessary tables upfront to avoid duplicate joins
    products_query = products_query.join(ProductPrice)
    products_query = products_query.join(Store)
    products_query = products_query.join(SubCategory)
    products_query = products_query.join(Category)

    # Eager load related data to minimize database queries
    products_query = products_query.options(
        joinedload(Product.sub_category).joinedload(SubCategory.category),
        joinedload(Product.prices).joinedload(ProductPrice.store),
        joinedload(Product.prices).joinedload(ProductPrice.location)
    )

    # Filter by search query if provided
    if query:
        # Use full-text search
        search_vector = func.to_tsvector('english', func.concat_ws(' ', Product.name, SubCategory.name, Category.name))
        search_query = func.plainto_tsquery('english', query)
        products_query = products_query.filter(search_vector.op('@@')(search_query))

    # Filter by category if selected
    if category_filter:
        products_query = products_query.filter(Category.name == category_filter)

    # Filter by store if selected
    if store_filter:
        products_query = products_query.filter(Store.name == store_filter)

    # Use aggregate function to get the minimum price per product
    products_query = products_query.add_columns(func.min(ProductPrice.price).label('min_price'))

    # Group by product to handle the aggregation
    products_query = products_query.group_by(Product.product_id)

    # Sort products by price
    if order_by == 'desc':
        products_query = products_query.order_by(desc('min_price'))
    else:
        products_query = products_query.order_by(asc('min_price'))

    # Paginate the products
    products_pagination = products_query.paginate(page=page, per_page=per_page, error_out=False)

    # Get distinct categories for the dropdown filter
    categories = Category.query.order_by(Category.name.asc()).all()

    # Get distinct stores for the store filter
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
                           total_pages=products_pagination.pages)

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

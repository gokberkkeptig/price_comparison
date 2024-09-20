from app import db
from sqlalchemy import UniqueConstraint, ForeignKey
from datetime import datetime

class Store(db.Model):
    __tablename__ = 'stores'
    store_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    # Relationships
    prices = db.relationship('ProductPrice', back_populates='store')

    def __repr__(self):
        return f'<Store {self.name}>'

class Location(db.Model):
    __tablename__ = 'locations'
    location_id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=False, default='Italy')
    # Relationships
    prices = db.relationship('ProductPrice', back_populates='location')

    __table_args__ = (
        UniqueConstraint('city', 'country', name='_city_country_uc'),
    )

    def __repr__(self):
        return f'<Location {self.city}, {self.country}>'

class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    # Relationships
    sub_categories = db.relationship('SubCategory', back_populates='category')

    def __repr__(self):
        return f'<Category {self.name}>'

class SubCategory(db.Model):
    __tablename__ = 'sub_categories'
    sub_category_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String, nullable=False)
    # Relationships
    category = db.relationship('Category', back_populates='sub_categories')
    products = db.relationship('Product', back_populates='sub_category')

    __table_args__ = (
        UniqueConstraint('name', 'category_id', name='_sub_category_uc'),
    )

    def __repr__(self):
        return f'<SubCategory {self.name} (Category {self.category.name})>'

class Product(db.Model):
    __tablename__ = 'products'
    product_id = db.Column(db.Integer, primary_key=True)
    sub_category_id = db.Column(db.Integer, db.ForeignKey('sub_categories.sub_category_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String, nullable=False)
    link = db.Column(db.String)
    image_url = db.Column(db.String)
    # Relationships
    sub_category = db.relationship('SubCategory', back_populates='products')
    prices = db.relationship('ProductPrice', back_populates='product')

    __table_args__ = (
        UniqueConstraint('name', 'sub_category_id', name='_product_uc'),
    )

    def __repr__(self):
        return f'<Product {self.name} (SubCategory {self.sub_category.name})>'

class ProductPrice(db.Model):
    __tablename__ = 'product_prices'
    price_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id', ondelete='CASCADE'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id', ondelete='CASCADE'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)
    # Relationships
    product = db.relationship('Product', back_populates='prices')
    store = db.relationship('Store', back_populates='prices')
    location = db.relationship('Location', back_populates='prices')

    __table_args__ = (
        UniqueConstraint('product_id', 'store_id', 'location_id', name='_price_uc'),
    )

    def __repr__(self):
        return f'<ProductPrice {self.price} for Product {self.product.name} at Store {self.store.name} in {self.location.city}>'

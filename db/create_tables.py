import os
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, TIMESTAMP
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# SQLAlchemy setup for PostgreSQL
# Make sure to set your actual PostgreSQL database URI
DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://username:password@localhost:5432/your_database')

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
    prices = relationship('ProductPrice', back_populates='store')

# Define the Location model
class Location(Base):
    __tablename__ = 'locations'

    location_id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False, default='Italy')
    # Relationships
    prices = relationship('ProductPrice', back_populates='location')

    __table_args__ = (
        UniqueConstraint('city', 'country', name='_city_country_uc'),
    )

# Define the Category model
class Category(Base):
    __tablename__ = 'categories'

    category_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    # Relationships
    sub_categories = relationship('SubCategory', back_populates='category')

# Define the SubCategory model
class SubCategory(Base):
    __tablename__ = 'sub_categories'

    sub_category_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.category_id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    # Relationships
    category = relationship('Category', back_populates='sub_categories')
    products = relationship('Product', back_populates='sub_category')

    __table_args__ = (
        UniqueConstraint('name', 'category_id', name='_sub_category_uc'),
    )

# Define the Product model
class Product(Base):
    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True)
    sub_category_id = Column(Integer, ForeignKey('sub_categories.sub_category_id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    link = Column(String)
    image_url = Column(String)
    # Relationships
    sub_category = relationship('SubCategory', back_populates='products')
    prices = relationship('ProductPrice', back_populates='product')

    __table_args__ = (
        UniqueConstraint('name', 'sub_category_id', name='_product_uc'),
    )

# Define the ProductPrice model
class ProductPrice(Base):
    __tablename__ = 'product_prices'

    price_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.product_id', ondelete='CASCADE'), nullable=False)
    store_id = Column(Integer, ForeignKey('stores.store_id', ondelete='CASCADE'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.location_id', ondelete='CASCADE'), nullable=False)
    price = Column(Float, nullable=False)
    last_updated = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    # Relationships
    product = relationship('Product', back_populates='prices')
    store = relationship('Store', back_populates='prices')
    location = relationship('Location', back_populates='prices')

    __table_args__ = (
        UniqueConstraint('product_id', 'store_id', 'location_id', name='_price_uc'),
    )

if __name__ == "__main__":
    # Create all tables
    Base.metadata.create_all(engine)
    print("All tables created successfully!")

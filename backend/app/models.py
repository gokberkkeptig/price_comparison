from datetime import datetime, timezone

from app import db


class Store(db.Model):
    __tablename__ = "stores"

    store_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    prices = db.relationship("ProductPrice", back_populates="store", lazy="dynamic")

    def to_dict(self):
        return {"store_id": self.store_id, "name": self.name}


class Location(db.Model):
    __tablename__ = "locations"

    location_id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False, default="Italy")

    prices = db.relationship("ProductPrice", back_populates="location", lazy="dynamic")

    __table_args__ = (
        db.UniqueConstraint("city", "country", name="_city_country_uc"),
    )

    def to_dict(self):
        return {
            "location_id": self.location_id,
            "city": self.city,
            "country": self.country,
        }


class Category(db.Model):
    __tablename__ = "categories"

    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    sub_categories = db.relationship("SubCategory", back_populates="category", lazy="dynamic")

    def to_dict(self):
        return {"category_id": self.category_id, "name": self.name}


class SubCategory(db.Model):
    __tablename__ = "sub_categories"

    sub_category_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.category_id", ondelete="CASCADE"),
        nullable=False,
    )
    name = db.Column(db.String(150), nullable=False)

    category = db.relationship("Category", back_populates="sub_categories")
    products = db.relationship("Product", back_populates="sub_category", lazy="dynamic")

    __table_args__ = (
        db.UniqueConstraint("name", "category_id", name="_sub_category_uc"),
    )

    def to_dict(self):
        return {
            "sub_category_id": self.sub_category_id,
            "category_id": self.category_id,
            "name": self.name,
            "category": self.category.name if self.category else None,
        }


class Product(db.Model):
    __tablename__ = "products"

    product_id = db.Column(db.Integer, primary_key=True)
    sub_category_id = db.Column(
        db.Integer,
        db.ForeignKey("sub_categories.sub_category_id", ondelete="CASCADE"),
        nullable=False,
    )
    name = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(500))
    image_url = db.Column(db.String(500))

    sub_category = db.relationship("SubCategory", back_populates="products")
    prices = db.relationship("ProductPrice", back_populates="product", lazy="selectin")

    __table_args__ = (
        db.UniqueConstraint("name", "sub_category_id", name="_product_uc"),
    )

    def to_dict(self, include_prices=False):
        data = {
            "product_id": self.product_id,
            "name": self.name,
            "image_url": self.image_url,
            "link": self.link,
            "sub_category": self.sub_category.name if self.sub_category else None,
            "category": (
                self.sub_category.category.name
                if self.sub_category and self.sub_category.category
                else None
            ),
        }
        if include_prices:
            data["prices"] = [p.to_dict() for p in self.prices]
            if self.prices:
                data["min_price"] = min(p.price for p in self.prices)
            else:
                data["min_price"] = None
        return data


class ProductPrice(db.Model):
    __tablename__ = "product_prices"

    price_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.product_id", ondelete="CASCADE"),
        nullable=False,
    )
    store_id = db.Column(
        db.Integer,
        db.ForeignKey("stores.store_id", ondelete="CASCADE"),
        nullable=False,
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("locations.location_id", ondelete="CASCADE"),
        nullable=False,
    )
    price = db.Column(db.Float, nullable=False)
    last_updated = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    product = db.relationship("Product", back_populates="prices")
    store = db.relationship("Store", back_populates="prices")
    location = db.relationship("Location", back_populates="prices")

    __table_args__ = (
        db.UniqueConstraint("product_id", "store_id", "location_id", name="_price_uc"),
    )

    def to_dict(self):
        return {
            "price_id": self.price_id,
            "price": self.price,
            "store": self.store.name if self.store else None,
            "store_id": self.store_id,
            "city": self.location.city if self.location else None,
            "location_id": self.location_id,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

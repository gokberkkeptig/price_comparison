from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name="development"):
    app = Flask(__name__)

    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.products import products_bp
    from app.api.compare import compare_bp
    from app.api.cart import cart_bp
    from app.api.receipt import receipt_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(compare_bp, url_prefix="/api")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(receipt_bp, url_prefix="/api/receipt")

    # Register error handlers
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)

    return app

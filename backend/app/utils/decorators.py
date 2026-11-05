from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.models import User


def login_required(fn):
    """Decorator that verifies a valid JWT is present and loads the user."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401
        kwargs["current_user"] = user
        return fn(*args, **kwargs)

    return wrapper

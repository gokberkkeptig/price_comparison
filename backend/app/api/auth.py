from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from app import db
from app.models import User
from app.utils.decorators import login_required

import bcrypt

auth_bp = Blueprint("auth", __name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # Validation
    errors = {}
    if not username or len(username) < 3:
        errors["username"] = "Username must be at least 3 characters"
    if not email or "@" not in email:
        errors["email"] = "A valid email is required"
    if not password or len(password) < 6:
        errors["password"] = "Password must be at least 6 characters"
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 422

    # Check for existing user
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    # Accept either username or email for login
    login_id = (data.get("login") or data.get("email") or data.get("username") or "").strip()
    password = data.get("password") or ""

    if not login_id or not password:
        return jsonify({"error": "Login and password are required"}), 400

    # Find user by username or email
    user = User.query.filter(
        (User.username == login_id) | (User.email == login_id.lower())
    ).first()

    if not user or not check_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "token": token,
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me(current_user):
    return jsonify({"user": current_user.to_dict()}), 200

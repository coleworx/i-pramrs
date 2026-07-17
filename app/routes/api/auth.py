# app/routes/api/auth.py
from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.database import get_db

api_auth_bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@api_auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = (data.get("username") or "").strip()
    email    = (data.get("email")    or "").strip()
    password = data.get("password")  or ""

    if not username:
        return jsonify({"error": "Username is required."}), 400
    if not email:
        return jsonify({"error": "Email is required."}), 400
    if not password:
        return jsonify({"error": "Password is required."}), 400

    db = get_db()
    if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
        return jsonify({"error": "Username already taken."}), 409
    if db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
        return jsonify({"error": "Email already registered."}), 409

    db.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, generate_password_hash(password))
    )
    db.commit()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    session.clear()
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"user": {"id": user["id"], "username": user["username"], "email": user["email"]}}), 201


@api_auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password")  or ""
    db       = get_db()
    user     = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user is None or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid username or password."}), 401

    session.clear()
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"user": {"id": user["id"], "username": user["username"], "email": user["email"]}})


@api_auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out."})

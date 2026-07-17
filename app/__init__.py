# app/__init__.py
import os
import json
from flask import Flask, session, jsonify
from flask_cors import CORS
from app.models.database import init_db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = os.environ.get("SECRET_KEY", "ipramrs-dev-secret-change-in-production")

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "ipramrs.db")

    # Allow the React dev server (port 3000) to send cookies
    CORS(app,
         supports_credentials=True,
         origins=["http://localhost:3000", "http://127.0.0.1:3000"],
         allow_headers=["Content-Type"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    init_db(app)

    # ── Database Migration: ensure previous_status column exists ──
    import sqlite3 as _sqlite3
    _db_path = os.path.join(app.instance_path, "ipramrs.db")
    _conn = _sqlite3.connect(_db_path)
    _existing = [r[1] for r in _conn.execute("PRAGMA table_info(risks)").fetchall()]
    if "previous_status" not in _existing:
        _conn.execute("ALTER TABLE risks ADD COLUMN previous_status TEXT DEFAULT 'Open'")
        _conn.execute("UPDATE risks SET previous_status = status")
        _conn.commit()
    _conn.close()


    # ── JSON template filter (kept for any remaining Jinja templates) ──

    @app.template_filter("from_json")
    def from_json_filter(value):
        if not value:
            return []
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return []

    # ── /api/me — current user endpoint ───────────────────────────────
    @app.route("/api/me")
    def me():
        if "user_id" not in session:
            return jsonify({"error": "Not authenticated."}), 401
        return jsonify({"user": {"id": session["user_id"], "username": session["username"]}})

    # ── PDF Reports blueprint ──────────────────────────────────────────
    from app.routes.reports import reports_bp
    app.register_blueprint(reports_bp)

    # ── JSON API blueprints ────────────────────────────────────────────
    from app.routes.api.auth      import api_auth_bp
    from app.routes.api.projects  import api_projects_bp
    from app.routes.api.risks     import api_risks_bp
    from app.routes.api.dashboard import api_dashboard_bp

    app.register_blueprint(api_auth_bp)
    app.register_blueprint(api_projects_bp)
    app.register_blueprint(api_risks_bp)
    app.register_blueprint(api_dashboard_bp)

    return app

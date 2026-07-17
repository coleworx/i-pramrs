# app/__init__.py
import os
from flask import Flask
from app.models.database import init_db


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = os.environ.get("SECRET_KEY", "ipramrs-dev-secret-change-in-production")

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "ipramrs.db")

    init_db(app)

    from app.routes.auth import auth_bp
    from app.routes.projects import projects_bp
    from app.routes.risks import risks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(risks_bp)

    return app

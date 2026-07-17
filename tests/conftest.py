"""
conftest.py
Shared pytest fixtures for I-PRAMRS test suite.
"""
import os
import tempfile
import pytest
from app import create_app
from app.models.database import get_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    flask_app = create_app()
    flask_app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
    })

    with flask_app.app_context():
        from app.models.database import init_db
        init_db(flask_app)

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def registered_user(client):
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    })
    return {"username": "testuser", "password": "testpass123"}


@pytest.fixture
def logged_in_client(client, registered_user):
    client.post("/api/auth/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"],
    })
    return client

"""
test_auth.py
Integration tests for registration, login, and logout API flows.
"""
import pytest


class TestAuth:

    def test_successful_registration(self, client):
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
        })
        assert response.status_code == 201
        data = response.get_json()
        assert "user" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "new@example.com"
        assert "id" in data["user"]

    def test_duplicate_username_rejected(self, client, registered_user):
        response = client.post("/api/auth/register", json={
            "username": registered_user["username"],
            "email": "different@example.com",
            "password": "anotherpass",
        })
        assert response.status_code == 409
        data = response.get_json()
        assert "error" in data
        assert "already taken" in data["error"].lower()

    def test_successful_login(self, client, registered_user):
        response = client.post("/api/auth/login", json={
            "username": registered_user["username"],
            "password": registered_user["password"],
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "user" in data
        assert data["user"]["username"] == registered_user["username"]

    def test_invalid_login_rejected(self, client, registered_user):
        response = client.post("/api/auth/login", json={
            "username": registered_user["username"],
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert "invalid" in data["error"].lower()

    def test_logout_clears_session(self, logged_in_client):
        response = logged_in_client.post("/api/auth/logout")
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Logged out."

        # Accessing a protected API endpoint after logout should return 401
        protected = logged_in_client.get("/api/projects")
        assert protected.status_code == 401
        assert "error" in protected.get_json()

    def test_unauthenticated_access_rejected(self, client):
        response = client.get("/api/projects")
        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert "authentication required" in data["error"].lower()

"""
test_projects_and_risks.py
Integration tests for the core end-to-end flow: project creation,
risk logging, ML classification, mitigation recommendation, feedback,
and status cascading.
"""
import pytest
import json


class TestProjects:

    def test_create_project(self, logged_in_client):
        response = logged_in_client.post("/api/projects", json={
            "name": "Test SME Project",
            "description": "A test project for pytest verification.",
            "sector": "Retail",
            "location": "Lusaka",
        })
        assert response.status_code == 201
        data = response.get_json()
        assert "message" in data
        assert "created" in data["message"]

    def test_project_requires_name(self, logged_in_client):
        response = logged_in_client.post("/api/projects", json={
            "name": "",
            "description": "Missing name.",
        })
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "name is required" in data["error"].lower()

    def test_projects_index_shows_created_project(self, logged_in_client):
        logged_in_client.post("/api/projects", json={"name": "Index Test Project"})
        response = logged_in_client.get("/api/projects")
        assert response.status_code == 200
        data = response.get_json()
        assert "projects" in data
        names = [p["name"] for p in data["projects"]]
        assert "Index Test Project" in names


class TestRisksEndToEnd:

    def _create_project(self, client, name="Risk Flow Project"):
        response = client.post("/api/projects", json={
            "name": name,
            "sector": "ICT/Software Services",
            "location": "Lusaka",
        })
        assert response.status_code == 201
        with client.application.app_context():
            from app.models.database import get_db
            db = get_db()
            row = db.execute(
                "SELECT id FROM projects WHERE name = ? ORDER BY id DESC LIMIT 1", (name,)
            ).fetchone()
            return row["id"]

    def test_log_risk_produces_classification_and_mitigations(self, logged_in_client, app):
        project_id = self._create_project(logged_in_client, "E2E Risk Project")

        response = logged_in_client.post(f"/api/risks/new/{project_id}", json={
            "title": "ZESCO load shedding affecting server uptime",
            "description": "Frequent load shedding is disrupting operations at the branch, causing server downtime and delaying the rollout.",
            "risk_category": "External/Stakeholder",
            "probability": 0.7,
            "impact": 0.65,
        })

        assert response.status_code == 201
        data = response.get_json()
        assert "risk_id" in data
        assert "severity" in data
        assert data["severity"] in ["Low", "Medium", "High", "Critical"]
        assert "confidence" in data
        risk_id = data["risk_id"]

        # Fetch risk details via GET /api/risks/<risk_id> to assert mitigations
        detail_res = logged_in_client.get(f"/api/risks/{risk_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.get_json()
        assert "risk" in detail_data
        assert "classification" in detail_data
        assert "mitigations" in detail_data
        assert len(detail_data["mitigations"]) == 3

    def test_feedback_correction_is_logged(self, logged_in_client, app):
        project_id = self._create_project(logged_in_client, "Feedback Test Project")

        res = logged_in_client.post(f"/api/risks/new/{project_id}", json={
            "title": "Test risk for feedback",
            "description": "A test risk description for verifying feedback logging works correctly.",
            "risk_category": "Technical",
            "probability": 0.5,
            "impact": 0.5,
        })
        assert res.status_code == 201
        risk_id = res.get_json()["risk_id"]

        response = logged_in_client.post(f"/api/risks/{risk_id}/feedback", json={
            "corrected_label": "High",
            "correction_reason": "Underestimated due to recent incidents.",
        })

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "Feedback recorded" in data["message"]

        # Verify feedback in DB/API
        detail_res = logged_in_client.get(f"/api/risks/{risk_id}")
        detail_data = detail_res.get_json()
        assert "feedback" in detail_data
        assert detail_data["feedback"] is not None
        assert detail_data["feedback"]["corrected_label"] == "High"
        assert detail_data["feedback"]["correction_reason"] == "Underestimated due to recent incidents."

    def test_project_toggle_status_and_delete(self, logged_in_client, app):
        project_id = self._create_project(logged_in_client, "Toggle Project")

        # 1. Close Project
        response = logged_in_client.post(f"/api/projects/{project_id}/toggle-status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "Closed"

        # 2. Reopen Project
        response = logged_in_client.post(f"/api/projects/{project_id}/toggle-status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "Active"

        # 3. Delete Project
        response = logged_in_client.post(f"/api/projects/{project_id}/delete")
        assert response.status_code == 200
        data = response.get_json()
        assert "deleted" in data["message"].lower()

        # Verify it's gone from database
        with app.app_context():
            from app.models.database import get_db
            db = get_db()
            row = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
            assert row is None

    def test_risk_toggle_status_and_delete(self, logged_in_client, app):
        project_id = self._create_project(logged_in_client, "Risk Action Project")

        # Create a risk
        res = logged_in_client.post(f"/api/risks/new/{project_id}", json={
            "title": "Action Risk",
            "description": "A risk description to verify status toggling and deletion.",
            "risk_category": "Technical",
            "probability": 0.5,
            "impact": 0.5,
        })
        assert res.status_code == 201
        risk_id = res.get_json()["risk_id"]

        # 1. Close Risk
        response = logged_in_client.post(f"/api/risks/{risk_id}/toggle-status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "Closed"

        # 2. Reopen Risk
        response = logged_in_client.post(f"/api/risks/{risk_id}/toggle-status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "Open"

        # 3. Delete Risk
        response = logged_in_client.post(f"/api/risks/{risk_id}/delete")
        assert response.status_code == 200
        data = response.get_json()
        assert "deleted" in data["message"].lower()

        # Verify risk and dependencies are gone
        with app.app_context():
            from app.models.database import get_db
            db = get_db()
            row = db.execute("SELECT * FROM risks WHERE id = ?", (risk_id,)).fetchone()
            assert row is None
            classification = db.execute("SELECT * FROM risk_classifications WHERE risk_id = ?", (risk_id,)).fetchone()
            assert classification is None

    def test_project_status_cascade(self, logged_in_client, app):
        # 1. Create a project
        project_id = self._create_project(logged_in_client, "Cascade Test Project")

        # 2. Create Risk A (defaults to 'Open')
        res_a = logged_in_client.post(f"/api/risks/new/{project_id}", json={
            "title": "Risk A",
            "description": "Risk A description for cascade tests.",
            "risk_category": "Technical",
            "probability": 0.4,
            "impact": 0.5,
        })
        assert res_a.status_code == 201
        risk_a_id = res_a.get_json()["risk_id"]

        # 3. Create Risk B (defaults to 'Open')
        res_b = logged_in_client.post(f"/api/risks/new/{project_id}", json={
            "title": "Risk B",
            "description": "Risk B description for cascade tests.",
            "risk_category": "Technical",
            "probability": 0.6,
            "impact": 0.7,
        })
        assert res_b.status_code == 201
        risk_b_id = res_b.get_json()["risk_id"]

        # 4. Toggle Risk B to 'Closed'
        res_toggle_b = logged_in_client.post(f"/api/risks/{risk_b_id}/toggle-status")
        assert res_toggle_b.status_code == 200
        assert res_toggle_b.get_json()["status"] == "Closed"

        # 5. Verify pre-closure status in DB
        with app.app_context():
            from app.models.database import get_db
            db = get_db()
            risk_a = db.execute("SELECT * FROM risks WHERE id = ?", (risk_a_id,)).fetchone()
            risk_b = db.execute("SELECT * FROM risks WHERE id = ?", (risk_b_id,)).fetchone()
            assert risk_a["status"] == "Open"
            assert risk_b["status"] == "Closed"

        # 6. Toggle Project to 'Closed'
        res_toggle_proj = logged_in_client.post(f"/api/projects/{project_id}/toggle-status")
        assert res_toggle_proj.status_code == 200
        assert res_toggle_proj.get_json()["status"] == "Closed"

        # 7. Verify both risks are now closed and previous_status is populated
        with app.app_context():
            db = get_db()
            risk_a = db.execute("SELECT * FROM risks WHERE id = ?", (risk_a_id,)).fetchone()
            risk_b = db.execute("SELECT * FROM risks WHERE id = ?", (risk_b_id,)).fetchone()
            # Both should be Closed
            assert risk_a["status"] == "Closed"
            assert risk_b["status"] == "Closed"
            # Previous status should be saved
            assert risk_a["previous_status"] == "Open"
            assert risk_b["previous_status"] == "Closed"

        # 8. Reopen Project (Active)
        res_toggle_proj_open = logged_in_client.post(f"/api/projects/{project_id}/toggle-status")
        assert res_toggle_proj_open.status_code == 200
        assert res_toggle_proj_open.get_json()["status"] == "Active"

        # 9. Verify risks statuses are restored to their previous_status
        with app.app_context():
            db = get_db()
            risk_a = db.execute("SELECT * FROM risks WHERE id = ?", (risk_a_id,)).fetchone()
            risk_b = db.execute("SELECT * FROM risks WHERE id = ?", (risk_b_id,)).fetchone()
            # Risk A should be restored to Open
            assert risk_a["status"] == "Open"
            # Risk B should be restored to Closed
            assert risk_b["status"] == "Closed"

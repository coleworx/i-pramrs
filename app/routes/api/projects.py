# app/routes/api/projects.py
from flask import Blueprint, request, session, jsonify
from app.models.database import get_db

api_projects_bp = Blueprint("api_projects", __name__, url_prefix="/api/projects")


def _require_auth():
    if "user_id" not in session:
        return jsonify({"error": "Authentication required."}), 401
    return None


def _row_to_dict(row):
    return dict(row) if row else None


@api_projects_bp.route("", methods=["GET"])
def index():
    err = _require_auth()
    if err: return err
    db = get_db()
    rows = db.execute(
        "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()
    return jsonify({"projects": [_row_to_dict(r) for r in rows]})


@api_projects_bp.route("", methods=["POST"])
def create():
    err = _require_auth()
    if err: return err
    data = request.get_json()
    name        = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    sector      = (data.get("sector") or "")
    location    = (data.get("location") or "")
    if not name:
        return jsonify({"error": "Project name is required."}), 400
    db = get_db()
    db.execute(
        "INSERT INTO projects (user_id, name, description, sector, location) VALUES (?,?,?,?,?)",
        (session["user_id"], name, description, sector, location)
    )
    db.commit()
    return jsonify({"message": f"Project '{name}' created."}), 201


@api_projects_bp.route("/<int:project_id>", methods=["GET"])
def detail(project_id):
    err = _require_auth()
    if err: return err
    db = get_db()
    project = db.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    ).fetchone()
    if project is None:
        return jsonify({"error": "Project not found."}), 404
    risks = db.execute(
        """SELECT r.*, rc.predicted_label, rc.confidence
           FROM risks r
           LEFT JOIN risk_classifications rc ON rc.risk_id = r.id
             AND rc.id = (SELECT MAX(id) FROM risk_classifications WHERE risk_id = r.id)
           WHERE r.project_id = ?
           ORDER BY r.created_at DESC""",
        (project_id,)
    ).fetchall()
    return jsonify({"project": _row_to_dict(project), "risks": [_row_to_dict(r) for r in risks]})


@api_projects_bp.route("/<int:project_id>/toggle-status", methods=["POST"])
def toggle_status(project_id):
    err = _require_auth()
    if err: return err
    db = get_db()
    project = db.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?",
                         (project_id, session["user_id"])).fetchone()
    if project is None:
        return jsonify({"error": "Project not found."}), 404
    new_status = "Closed" if project["status"] == "Active" else "Active"
    db.execute("UPDATE projects SET status = ? WHERE id = ?", (new_status, project_id))
    if new_status == "Closed":
        db.execute("UPDATE risks SET previous_status = status WHERE project_id = ?", (project_id,))
        db.execute("UPDATE risks SET status = 'Closed' WHERE project_id = ?", (project_id,))
    else:
        db.execute("UPDATE risks SET status = previous_status WHERE project_id = ?", (project_id,))
    db.commit()


    return jsonify({"message": f"Status updated to {new_status}.", "status": new_status})


@api_projects_bp.route("/<int:project_id>/delete", methods=["POST"])
def delete(project_id):
    err = _require_auth()
    if err: return err
    db = get_db()
    project = db.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?",
                         (project_id, session["user_id"])).fetchone()
    if project is None:
        return jsonify({"error": "Project not found."}), 404
    risks = db.execute("SELECT id FROM risks WHERE project_id = ?", (project_id,)).fetchall()
    risk_ids = [r["id"] for r in risks]
    if risk_ids:
        placeholders = ",".join("?" for _ in risk_ids)
        db.execute(f"DELETE FROM feedback_log WHERE risk_id IN ({placeholders})", risk_ids)
        db.execute(f"DELETE FROM mitigations WHERE risk_id IN ({placeholders})", risk_ids)
        db.execute(f"DELETE FROM risk_classifications WHERE risk_id IN ({placeholders})", risk_ids)
        db.execute(f"DELETE FROM risks WHERE id IN ({placeholders})", risk_ids)
    db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    db.commit()
    return jsonify({"message": "Project deleted."})


@api_projects_bp.route("/<int:project_id>/pdf", methods=["GET"])
def pdf(project_id):
    """Delegate to the existing reports blueprint."""
    from flask import redirect, url_for
    return redirect(url_for("reports.project_pdf", project_id=project_id))


@api_projects_bp.route("/<int:project_id>", methods=["PUT"])
def update(project_id):
    err = _require_auth()
    if err: return err
    data = request.get_json()
    name        = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    sector      = (data.get("sector") or "")
    location    = (data.get("location") or "")
    if not name:
        return jsonify({"error": "Project name is required."}), 400
    db = get_db()
    project = db.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?",
                         (project_id, session["user_id"])).fetchone()
    if project is None:
        return jsonify({"error": "Project not found."}), 404
    db.execute(
        "UPDATE projects SET name = ?, description = ?, sector = ?, location = ? WHERE id = ?",
        (name, description, sector, location, project_id)
    )
    db.commit()
    return jsonify({"message": f"Project '{name}' updated successfully."})


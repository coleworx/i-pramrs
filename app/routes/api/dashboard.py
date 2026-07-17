# app/routes/api/dashboard.py
import csv
from pathlib import Path
from flask import Blueprint, session, jsonify
from app.models.database import get_db

api_dashboard_bp = Blueprint("api_dashboard", __name__, url_prefix="/api/dashboard")

PROJECT_ROOT   = Path(__file__).resolve().parents[3]
COMPARISON_CSV = PROJECT_ROOT / "data" / "evaluation" / "model_comparison.csv"
SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]
SEVERITY_COLORS = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#f97316", "Critical": "#ef4444"}


def _require_auth():
    if "user_id" not in session:
        return jsonify({"error": "Authentication required."}), 401
    return None


def _load_model_comparison():
    if not COMPARISON_CSV.exists():
        return []
    rows = []
    with open(COMPARISON_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({k: (float(v) if _is_float(v) else v) for k, v in row.items()})
    return rows


def _is_float(v):
    try: float(v); return True
    except (ValueError, TypeError): return False


@api_dashboard_bp.route("", methods=["GET"])
def index():
    err = _require_auth()
    if err: return err
    db      = get_db()
    user_id = session["user_id"]

    total_projects = db.execute(
        "SELECT COUNT(*) c FROM projects WHERE user_id = ?", (user_id,)
    ).fetchone()["c"]

    total_risks = db.execute(
        """SELECT COUNT(*) c FROM risks r
           JOIN projects p ON p.id = r.project_id WHERE p.user_id = ?""", (user_id,)
    ).fetchone()["c"]

    severity_rows = db.execute(
        """SELECT rc.predicted_label, COUNT(*) c
           FROM risk_classifications rc
           JOIN risks r ON r.id = rc.risk_id
           JOIN projects p ON p.id = r.project_id
           WHERE p.user_id = ?
             AND rc.id IN (SELECT MAX(id) FROM risk_classifications GROUP BY risk_id)
           GROUP BY rc.predicted_label""", (user_id,)
    ).fetchall()
    severity_counts = {row["predicted_label"]: row["c"] for row in severity_rows}
    for s in SEVERITY_ORDER:
        severity_counts.setdefault(s, 0)

    category_rows = db.execute(
        """SELECT r.risk_category, COUNT(*) c
           FROM risks r JOIN projects p ON p.id = r.project_id
           WHERE p.user_id = ? GROUP BY r.risk_category""", (user_id,)
    ).fetchall()
    category_counts = {row["risk_category"]: row["c"] for row in category_rows}

    total_classified = db.execute(
        """SELECT COUNT(*) c FROM risk_classifications rc
           JOIN risks r ON r.id = rc.risk_id
           JOIN projects p ON p.id = r.project_id WHERE p.user_id = ?""", (user_id,)
    ).fetchone()["c"]

    total_corrected = db.execute(
        """SELECT COUNT(*) c FROM feedback_log fl
           JOIN risks r ON r.id = fl.risk_id
           JOIN projects p ON p.id = r.project_id WHERE p.user_id = ?""", (user_id,)
    ).fetchone()["c"]

    acceptance_rate = None
    if total_classified > 0:
        acceptance_rate = round(100 * (total_classified - total_corrected) / total_classified, 1)

    return jsonify({
        "total_projects":  total_projects,
        "total_risks":     total_risks,
        "severity_counts": severity_counts,
        "category_counts": category_counts,
        "total_classified": total_classified,
        "total_corrected":  total_corrected,
        "acceptance_rate":  acceptance_rate,
        "model_comparison": _load_model_comparison(),
    })


@api_dashboard_bp.route("/risk-matrix", methods=["GET"])
def risk_matrix():
    err = _require_auth()
    if err: return err
    db      = get_db()
    user_id = session["user_id"]

    rows = db.execute(
        """SELECT r.id, r.title, r.probability, r.impact, rc.predicted_label
           FROM risks r
           JOIN projects p ON p.id = r.project_id
           LEFT JOIN risk_classifications rc
             ON rc.risk_id = r.id
            AND rc.id = (SELECT MAX(id) FROM risk_classifications WHERE risk_id = r.id)
           WHERE p.user_id = ?""", (user_id,)
    ).fetchall()

    points_by_severity = {s: [] for s in SEVERITY_ORDER}
    for row in rows:
        label = row["predicted_label"] or "Low"
        points_by_severity.setdefault(label, []).append(
            {"x": row["probability"], "y": row["impact"], "title": row["title"]}
        )

    datasets = [
        {"label": label, "data": points_by_severity.get(label, []), "backgroundColor": SEVERITY_COLORS[label]}
        for label in SEVERITY_ORDER
    ]
    return jsonify({"datasets": datasets})

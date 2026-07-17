# app/routes/reports.py
import json
from functools import wraps
from flask import Blueprint, session, redirect, url_for, flash, send_file
from app.models.database import get_db
from app.reports.pdf_generator import generate_risk_report, generate_project_report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


@reports_bp.route("/risk/<int:risk_id>/pdf")
@login_required
def risk_pdf(risk_id):
    db = get_db()
    risk = db.execute(
        """SELECT r.*, p.name as project_name FROM risks r
           JOIN projects p ON p.id = r.project_id
           WHERE r.id = ? AND p.user_id = ?""",
        (risk_id, session["user_id"])
    ).fetchone()
    if risk is None:
        flash("Risk not found.", "danger")
        return redirect("/projects")


    classification = db.execute(
        "SELECT * FROM risk_classifications WHERE risk_id = ? ORDER BY created_at DESC LIMIT 1",
        (risk_id,)
    ).fetchone()

    mitigations = db.execute(
        "SELECT * FROM mitigations WHERE risk_id = ? ORDER BY rank_position",
        (risk_id,)
    ).fetchall()

    all_probs = {}
    if classification and classification["all_probs"]:
        all_probs = json.loads(classification["all_probs"])

    buffer = generate_risk_report(
        risk=dict(risk),
        classification=dict(classification) if classification else None,
        mitigations=[dict(m) for m in mitigations],
        all_probs=all_probs,
        project_name=risk["project_name"],
    )

    filename = f"IPRAMRS_Risk_{risk_id}_{risk['title'][:20].replace(' ', '_')}.pdf"
    return send_file(buffer, mimetype="application/pdf",
                      as_attachment=True, download_name=filename)


@reports_bp.route("/project/<int:project_id>/pdf")
@login_required
def project_pdf(project_id):
    db = get_db()
    project = db.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    ).fetchone()
    if project is None:
        flash("Project not found.", "danger")
        return redirect("/projects")

    risks = db.execute(
        """SELECT r.*, rc.predicted_label, rc.confidence
           FROM risks r
           LEFT JOIN risk_classifications rc
             ON rc.risk_id = r.id
            AND rc.id = (SELECT MAX(id) FROM risk_classifications WHERE risk_id = r.id)
           WHERE r.project_id = ?
           ORDER BY r.created_at DESC""",
        (project_id,)
    ).fetchall()

    buffer = generate_project_report(
        project=dict(project),
        risks=[dict(r) for r in risks],
    )

    filename = f"IPRAMRS_Project_{project['name'][:20].replace(' ', '_')}.pdf"
    return send_file(buffer, mimetype="application/pdf",
                      as_attachment=True, download_name=filename)

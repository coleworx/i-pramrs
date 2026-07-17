# app/routes/api/risks.py
import json
from flask import Blueprint, request, session, jsonify, redirect, url_for
from app.models.database import get_db
from app.ml.classifier import classify
from app.ml.recommender import recommend

api_risks_bp = Blueprint("api_risks", __name__, url_prefix="/api/risks")


def _require_auth():
    if "user_id" not in session:
        return jsonify({"error": "Authentication required."}), 401
    return None


def _row(r):
    return dict(r) if r else None


@api_risks_bp.route("/new/<int:project_id>", methods=["POST"])
def new(project_id):
    err = _require_auth()
    if err: return err
    db = get_db()
    project = db.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?",
                         (project_id, session["user_id"])).fetchone()
    if project is None:
        return jsonify({"error": "Project not found."}), 404

    data        = request.get_json()
    title       = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    category    = data.get("risk_category") or ""
    probability = float(data.get("probability", 0.5))
    impact      = float(data.get("impact", 0.5))

    if not title or not description:
        return jsonify({"error": "Title and description are required."}), 400
    if not category:
        return jsonify({"error": "Risk category is required."}), 400

    result     = classify(description, probability, impact)
    severity   = result["severity"]
    confidence = result["confidence"]
    all_probs  = result["all_probs"]

    mitigations = recommend(description, category, severity, top_n=3)

    cur = db.execute(
        "INSERT INTO risks (project_id, title, description, risk_category, probability, impact) VALUES (?,?,?,?,?,?)",
        (project_id, title, description, category, probability, impact)
    )
    risk_id = cur.lastrowid

    db.execute(
        "INSERT INTO risk_classifications (risk_id, predicted_label, confidence, all_probs) VALUES (?,?,?,?)",
        (risk_id, severity, confidence, json.dumps(all_probs))
    )

    for rank, m in enumerate(mitigations, 1):
        db.execute(
            """INSERT INTO mitigations (risk_id, mitigation_id, description, implementation_steps, source, similarity_score, rank_position)
               VALUES (?,?,?,?,?,?,?)""",
            (risk_id, m["id"], m["description"], json.dumps(m.get("implementation_steps", [])),
             m["source"], m["similarity_score"], rank)
        )
    db.commit()
    return jsonify({"message": "Risk classified.", "risk_id": risk_id, "severity": severity, "confidence": confidence}), 201


@api_risks_bp.route("/<int:risk_id>", methods=["GET"])
def detail(risk_id):
    err = _require_auth()
    if err: return err
    db = get_db()
    risk = db.execute(
        """SELECT r.*, p.name as project_name, p.id as project_id FROM risks r
           JOIN projects p ON p.id = r.project_id
           WHERE r.id = ? AND p.user_id = ?""",
        (risk_id, session["user_id"])
    ).fetchone()
    if risk is None:
        return jsonify({"error": "Risk not found."}), 404

    classification = db.execute(
        "SELECT * FROM risk_classifications WHERE risk_id = ? ORDER BY created_at DESC LIMIT 1",
        (risk_id,)
    ).fetchone()

    mitigations = db.execute(
        "SELECT * FROM mitigations WHERE risk_id = ? ORDER BY rank_position",
        (risk_id,)
    ).fetchall()

    feedback = db.execute(
        "SELECT * FROM feedback_log WHERE risk_id = ? ORDER BY created_at DESC LIMIT 1",
        (risk_id,)
    ).fetchone()

    all_probs = {}
    if classification and classification["all_probs"]:
        all_probs = json.loads(classification["all_probs"])

    mits = []
    for m in mitigations:
        md = dict(m)
        if isinstance(md.get("implementation_steps"), str):
            try:
                md["implementation_steps"] = json.loads(md["implementation_steps"])
            except Exception:
                md["implementation_steps"] = []
        mits.append(md)

    return jsonify({
        "risk":           _row(risk),
        "classification": _row(classification),
        "mitigations":    mits,
        "feedback":       _row(feedback),
        "all_probs":      all_probs,
    })


@api_risks_bp.route("/<int:risk_id>/feedback", methods=["POST"])
def feedback(risk_id):
    err = _require_auth()
    if err: return err
    db = get_db()
    risk = db.execute(
        """SELECT r.* FROM risks r JOIN projects p ON p.id = r.project_id
           WHERE r.id = ? AND p.user_id = ?""",
        (risk_id, session["user_id"])
    ).fetchone()
    if risk is None:
        return jsonify({"error": "Risk not found."}), 404

    data             = request.get_json()
    corrected_label  = data.get("corrected_label", "")
    correction_reason = (data.get("correction_reason") or "").strip()

    if not corrected_label:
        return jsonify({"error": "corrected_label is required."}), 400

    classification = db.execute(
        "SELECT * FROM risk_classifications WHERE risk_id = ? ORDER BY created_at DESC LIMIT 1",
        (risk_id,)
    ).fetchone()
    predicted_label = classification["predicted_label"] if classification else "Unknown"
    confidence      = classification["confidence"]      if classification else None

    db.execute(
        """INSERT INTO feedback_log (risk_id, predicted_label, corrected_label, confidence, correction_reason)
           VALUES (?,?,?,?,?)""",
        (risk_id, predicted_label, corrected_label, confidence, correction_reason)
    )
    db.execute("UPDATE risk_classifications SET accepted = 0 WHERE risk_id = ?", (risk_id,))
    db.commit()
    return jsonify({"message": "Feedback recorded."})


@api_risks_bp.route("/<int:risk_id>/toggle-status", methods=["POST"])
def toggle_status(risk_id):
    err = _require_auth()
    if err: return err
    db = get_db()
    risk = db.execute(
        """SELECT r.*, p.user_id FROM risks r
           JOIN projects p ON p.id = r.project_id
           WHERE r.id = ? AND p.user_id = ?""",
        (risk_id, session["user_id"])
    ).fetchone()
    if risk is None:
        return jsonify({"error": "Risk not found."}), 404
    new_status = "Closed" if risk["status"] == "Open" else "Open"
    db.execute(
        "UPDATE risks SET previous_status = status, status = ? WHERE id = ?",
        (new_status, risk_id)
    )
    db.commit()
    return jsonify({"message": f"Status updated to {new_status}.", "status": new_status})



@api_risks_bp.route("/<int:risk_id>/delete", methods=["POST"])
def delete(risk_id):
    err = _require_auth()
    if err: return err
    db = get_db()
    risk = db.execute(
        """SELECT r.*, p.user_id FROM risks r
           JOIN projects p ON p.id = r.project_id
           WHERE r.id = ? AND p.user_id = ?""",
        (risk_id, session["user_id"])
    ).fetchone()
    if risk is None:
        return jsonify({"error": "Risk not found."}), 404
    project_id = risk["project_id"]
    db.execute("DELETE FROM feedback_log WHERE risk_id = ?",         (risk_id,))
    db.execute("DELETE FROM mitigations WHERE risk_id = ?",          (risk_id,))
    db.execute("DELETE FROM risk_classifications WHERE risk_id = ?", (risk_id,))
    db.execute("DELETE FROM risks WHERE id = ?",                     (risk_id,))
    db.commit()
    return jsonify({"message": "Risk deleted.", "project_id": project_id})


@api_risks_bp.route("/<int:risk_id>/pdf", methods=["GET"])
def pdf(risk_id):
    return redirect(url_for("reports.risk_pdf", risk_id=risk_id))


@api_risks_bp.route("/<int:risk_id>", methods=["PUT"])
def update(risk_id):
    err = _require_auth()
    if err: return err
    data = request.get_json()
    title       = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    category    = data.get("risk_category") or ""
    probability = float(data.get("probability", 0.5))
    impact      = float(data.get("impact", 0.5))

    if not title or not description:
        return jsonify({"error": "Title and description are required."}), 400
    if not category:
        return jsonify({"error": "Risk category is required."}), 400

    db = get_db()
    risk = db.execute(
        """SELECT r.*, p.user_id FROM risks r
           JOIN projects p ON p.id = r.project_id
           WHERE r.id = ? AND p.user_id = ?""",
        (risk_id, session["user_id"])
    ).fetchone()
    if risk is None:
        return jsonify({"error": "Risk not found."}), 404

    # Determine if re-classification is required
    desc_changed = description != risk["description"]
    prob_changed = probability != risk["probability"]
    imp_changed  = impact != risk["impact"]
    cat_changed  = category != risk["risk_category"]

    db.execute(
        """UPDATE risks SET title = ?, description = ?, risk_category = ?, probability = ?, impact = ?
           WHERE id = ?""",
        (title, description, category, probability, impact, risk_id)
    )

    if desc_changed or prob_changed or imp_changed or cat_changed:
        result     = classify(description, probability, impact)
        severity   = result["severity"]
        confidence = result["confidence"]
        all_probs  = result["all_probs"]

        db.execute("DELETE FROM risk_classifications WHERE risk_id = ?", (risk_id,))
        db.execute("DELETE FROM mitigations WHERE risk_id = ?", (risk_id,))

        db.execute(
            "INSERT INTO risk_classifications (risk_id, predicted_label, confidence, all_probs) VALUES (?,?,?,?)",
            (risk_id, severity, confidence, json.dumps(all_probs))
        )

        mitigations = recommend(description, category, severity, top_n=3)
        for rank, m in enumerate(mitigations, 1):
            db.execute(
                """INSERT INTO mitigations (risk_id, mitigation_id, description, implementation_steps, source, similarity_score, rank_position)
                   VALUES (?,?,?,?,?,?,?)""",
                (risk_id, m["id"], m["description"], json.dumps(m.get("implementation_steps", [])),
                 m["source"], m["similarity_score"], rank)
            )

    db.commit()
    return jsonify({"message": "Risk updated successfully."})



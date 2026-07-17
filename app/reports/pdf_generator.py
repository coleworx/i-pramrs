"""
pdf_generator.py

Generates PDF reports for I-PRAMRS using ReportLab:
  1. generate_risk_report()    - single risk: description, ML classification, mitigations
  2. generate_project_report() - full project risk register summary

Reports are built in-memory (BytesIO) and streamed directly to the browser
via Flask's send_file, so no files are written to disk.
"""

import json
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)

SEVERITY_COLORS = {
    "Low": colors.HexColor("#198754"),
    "Medium": colors.HexColor("#fd7e14"),
    "High": colors.HexColor("#e67e22"),
    "Critical": colors.HexColor("#c0392b"),
}

PRIMARY = colors.HexColor("#1a1a2e")
ACCENT = colors.HexColor("#0f3460")


def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", fontSize=18, textColor=PRIMARY,
        spaceAfter=4, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="ReportSubtitle", fontSize=10, textColor=colors.grey, spaceAfter=14
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", fontSize=13, textColor=ACCENT,
        spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        name="BodySmall", fontSize=9.5, leading=13
    ))
    return styles


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2*cm, 1.2*cm,
        "I-PRAMRS — Intelligent Project Risk Assessment & Mitigation Recommendation System")
    canvas.drawRightString(A4[0] - 2*cm, 1.2*cm,
        f"Generated {datetime.now().strftime('%d %B %Y, %H:%M')}")
    canvas.restoreState()


def generate_risk_report(risk: dict, classification: dict, mitigations: list,
                          all_probs: dict, project_name: str) -> BytesIO:
    """Generate a single-risk PDF report. Returns a BytesIO buffer."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    styles = _base_styles()
    story = []

    story.append(Paragraph("I-PRAMRS Risk Assessment Report", styles["ReportTitle"]))
    story.append(Paragraph(f"Project: {project_name}", styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=1.2))

    story.append(Paragraph(risk["title"], styles["SectionHeading"]))
    story.append(Paragraph(risk["description"], styles["BodySmall"]))
    story.append(Spacer(1, 8))

    detail_table = Table([
        ["Category", risk["risk_category"]],
        ["Probability", f"{risk['probability']}"],
        ["Impact", f"{risk['impact']}"],
        ["Risk Score (P x I)", f"{risk['probability'] * risk['impact']:.3f}"],
        ["Logged", str(risk["created_at"])[:16]],
    ], colWidths=[5*cm, 10*cm])
    detail_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.lightgrey),
    ]))
    story.append(detail_table)

    if classification:
        story.append(Paragraph("ML Classification Result", styles["SectionHeading"]))
        sev = classification["predicted_label"]
        sev_color = SEVERITY_COLORS.get(sev, colors.black)

        cls_table = Table([
            ["Predicted Severity", sev],
            ["Model Confidence", f"{classification['confidence']*100:.1f}%"],
            ["Model", "Random Forest (200 estimators) — primary classifier"],
        ], colWidths=[5*cm, 10*cm])
        cls_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (1, 0), (1, 0), sev_color),
            ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ]))
        story.append(cls_table)

        if all_probs:
            story.append(Spacer(1, 6))
            prob_rows = [["Severity Class", "Probability"]]
            for label in ["Low", "Medium", "High", "Critical"]:
                prob_rows.append([label, f"{all_probs.get(label, 0)*100:.1f}%"])
            prob_table = Table(prob_rows, colWidths=[5*cm, 10*cm])
            prob_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(prob_table)

    if mitigations:
        story.append(Paragraph("Recommended Mitigation Strategies", styles["SectionHeading"]))
        for i, m in enumerate(mitigations, 1):
            story.append(Paragraph(
                f"<b>{i}. {m['description']}</b>", styles["BodySmall"]))
            steps = m.get("implementation_steps")
            if isinstance(steps, str):
                try:
                    steps = json.loads(steps)
                except (ValueError, TypeError):
                    steps = []
            if steps:
                for step in steps:
                    story.append(Paragraph(f"&nbsp;&nbsp;&bull; {step}", styles["BodySmall"]))
            story.append(Paragraph(
                f"<i>Source: {m['source']}</i>", styles["BodySmall"]))
            story.append(Spacer(1, 8))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer


def generate_project_report(project: dict, risks: list) -> BytesIO:
    """Generate a project-level risk register PDF summary. Returns a BytesIO buffer."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=2*cm, bottomMargin=2*cm,
                             leftMargin=2*cm, rightMargin=2*cm)
    styles = _base_styles()
    story = []

    story.append(Paragraph("I-PRAMRS Project Risk Register", styles["ReportTitle"]))
    story.append(Paragraph(
        f"{project['name']} — {project.get('sector', '') or 'N/A'}, {project.get('location', '') or 'N/A'}",
        styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=1.2))
    story.append(Spacer(1, 10))

    if project.get("description"):
        story.append(Paragraph(project["description"], styles["BodySmall"]))
        story.append(Spacer(1, 10))

    # Summary counts
    severity_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for r in risks:
        label = r.get("predicted_label") or "Low"
        severity_counts[label] = severity_counts.get(label, 0) + 1

    summary_row = ["Total Risks"] + list(severity_counts.keys())
    summary_val = [str(len(risks))] + [str(v) for v in severity_counts.values()]
    summary_table = Table([summary_row, summary_val], colWidths=[3*cm] + [3*cm]*4)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("Risk Register", styles["SectionHeading"]))

    rows = [["#", "Title", "Category", "P", "I", "Severity", "Confidence"]]
    for i, r in enumerate(risks, 1):
        rows.append([
            str(i), r["title"][:35], r["risk_category"],
            f"{r['probability']}", f"{r['impact']}",
            r.get("predicted_label") or "—",
            f"{r['confidence']*100:.0f}%" if r.get("confidence") else "—",
        ])

    register_table = Table(rows, colWidths=[1*cm, 5*cm, 3.5*cm, 1.3*cm, 1.3*cm, 2.2*cm, 2.2*cm])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i, r in enumerate(risks, 1):
        sev = r.get("predicted_label")
        if sev in SEVERITY_COLORS:
            style_cmds.append(("TEXTCOLOR", (5, i), (5, i), SEVERITY_COLORS[sev]))
            style_cmds.append(("FONTNAME", (5, i), (5, i), "Helvetica-Bold"))
    register_table.setStyle(TableStyle(style_cmds))
    story.append(register_table)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer

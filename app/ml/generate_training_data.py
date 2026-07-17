"""
generate_training_data.py

Generates a synthetic, labelled risk dataset for I-PRAMRS.

METHODOLOGY NOTE (for Chapter 3):
Risk descriptions are built compositionally from a Zambian SME risk vocabulary
(grounded in the PMI Risk Breakdown Structure categories: Technical, Schedule,
Cost/Financial, Resource/Staffing, Scope/Requirements, External/Stakeholder).
Probability and Impact are sampled per category from severity-tier-appropriate
ranges, and the final severity label (Low/Medium/High/Critical) is DERIVED from
a probability x impact risk score using thresholds consistent with an
ISO 31000-style risk matrix. This means:
  - Labels are principled and reproducible (not hand-assigned)
  - Text vocabulary correlates with, but does not perfectly determine, severity
    (introducing realistic label noise/ambiguity)
  - The vocabulary itself is grounded in real Zambian SME operating conditions
    (ZESCO load shedding, ZMW/USD depreciation, ZRA customs delays, mobile money
    integration, rural connectivity, rainy-season logistics, etc.)

Output: data/processed/training_data.csv
Columns: risk_id, project_id, sector, location, risk_category,
         risk_description, probability, impact, severity_label
"""

import csv
import random
from pathlib import Path

random.seed(42)  # reproducibility for dissertation methodology section

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TARGET_ROWS = 420

SECTORS = [
    "agribusiness", "retail", "construction", "manufacturing",
    "ICT/software services", "logistics", "hospitality", "mining supply chain",
]

LOCATIONS = [
    "Lusaka", "Ndola", "Kitwe", "Livingstone",
    "Chipata", "Solwezi", "Kabwe", "Choma",
]

PROJECTS = [
    "the new inventory management system", "the mobile money integration",
    "the warehouse expansion project", "the e-commerce platform rollout",
    "the staff training programme", "the solar power installation",
    "the customer database migration", "the point-of-sale upgrade",
    "the branch network expansion", "the financial reporting system",
]

# Tier-level phrasing (shared across categories) -----------------------------

INTENSITY_INTRO = {
    "low": ["A minor", "A small", "A slight"],
    "medium": ["A moderate", "A noticeable", "A growing"],
    "high": ["A serious", "A major", "A significant"],
    "critical": ["A critical", "A severe", "A potentially catastrophic"],
}

CONSEQUENCE = {
    "low": [
        "was identified early and resolved with minimal effort",
        "caused only a brief delay to {project}",
        "required minor adjustments but did not affect the overall plan for {project}",
    ],
    "medium": [
        "could delay {project} by one to two weeks if not addressed promptly",
        "is likely to require additional resources to keep {project} on track",
        "has raised concerns among the project team about the quality of {project}",
    ],
    "high": [
        "threatens to push {project} significantly behind schedule",
        "could substantially increase the overall cost of {project}",
        "may require escalation to senior management to resolve issues with {project}",
    ],
    "critical": [
        "could halt {project} entirely until resolved",
        "poses a serious risk to the successful completion of {project}",
        "may result in the SME abandoning {project} altogether",
    ],
}

# Category-specific issue phrases (noun phrases) -----------------------------

ISSUES = {
    "Technical": [
        "a software bug discovered in the core module of {project}",
        "a compatibility issue between {project} and the existing point-of-sale hardware",
        "a delay in integrating {project} with mobile money APIs (MTN/Airtel)",
        "system downtime caused by ZESCO load shedding affecting servers running {project}",
        "a security vulnerability discovered in the authentication module of {project}",
        "a licensing conflict with third-party software used in {project}",
        "a performance bottleneck in {project} under the low-bandwidth conditions typical in {location}",
        "a data loss incident during the migration of records for {project}",
    ],
    "Schedule": [
        "a delay in the delivery of imported equipment for {project} pending ZRA customs clearance",
        "a contractor delay affecting the implementation timeline of {project}",
        "a dependency on an external consultant whose availability is delaying {project}",
        "scope creep that is pushing back the planned milestones for {project}",
        "rainy-season disruptions to site logistics for {project} in {location}",
        "a delay in stakeholder sign-off on a key milestone for {project}",
        "the user-acceptance testing phase for {project} taking longer than planned",
        "rescheduled staff training sessions delaying the rollout of {project}",
    ],
    "Cost/Financial": [
        "ZMW depreciation against the US dollar increasing the cost of software licences for {project}",
        "a budget overrun caused by unforeseen consulting fees on {project}",
        "import duties on hardware for {project} being higher than originally estimated",
        "a supplier price increase affecting the procurement plan for {project}",
        "additional costs arising from an extended timeline for {project}",
        "currency exchange losses on international payments related to {project}",
        "underestimated cloud hosting costs for {project}",
        "depletion of the contingency reserve allocated to {project}",
    ],
    "Resource/Staffing": [
        "a shortage of skilled ICT staff in {location} able to support {project}",
        "the resignation of a key team member midway through {project}",
        "inadequate training of end-users ahead of the {project} rollout",
        "scheduling conflicts with contractors assigned to {project}",
        "high staff turnover during the implementation of {project}",
        "over-reliance on a single subject-matter expert for {project}",
        "insufficient project management capacity to oversee {project}",
        "reliance on part-time staff to support {project} after hours",
    ],
    "Scope/Requirements": [
        "unclear requirements from management regarding the scope of {project}",
        "frequent change requests from stakeholders affecting {project}",
        "additional feature requests expanding the original scope of {project}",
        "a misalignment between business requirements and the technical design of {project}",
        "incomplete requirements gathering due to limited stakeholder availability for {project}",
        "conflicting priorities among departments regarding {project}",
        "an underestimation of the complexity of business processes covered by {project}",
        "a lack of documented standard operating procedures needed to configure {project}",
    ],
    "External/Stakeholder": [
        "frequent ZESCO load shedding affecting day-to-day operations during {project}",
        "unreliable internet connectivity at branch locations in {location} supporting {project}",
        "a change in data protection regulations affecting the design of {project}",
        "a logistics disruption during the rainy season affecting deliveries for {project}",
        "broader economic instability affecting business confidence in {project}",
        "delays in approvals from an external stakeholder (e.g. a bank or regulator) needed for {project}",
        "a security incident at the project site affecting {project}",
        "dependency on a single internet service provider with no backup link for {project}",
    ],
}

CATEGORIES = list(ISSUES.keys())

# Probability / impact sampling ranges per severity tier ---------------------

PI_RANGES = {
    "low":      {"prob": (0.05, 0.35), "impact": (0.05, 0.35)},
    "medium":   {"prob": (0.25, 0.55), "impact": (0.25, 0.55)},
    "high":     {"prob": (0.45, 0.75), "impact": (0.45, 0.80)},
    "critical": {"prob": (0.60, 0.95), "impact": (0.60, 0.95)},
}

TIER_WEIGHTS = {"low": 0.25, "medium": 0.35, "high": 0.25, "critical": 0.15}


def severity_from_score(prob: float, impact: float) -> str:
    """ISO 31000-style risk matrix: severity derived from probability x impact."""
    score = prob * impact
    if score < 0.08:
        return "Low"
    elif score < 0.22:
        return "Medium"
    elif score < 0.45:
        return "High"
    else:
        return "Critical"


def weighted_tier() -> str:
    tiers, weights = zip(*TIER_WEIGHTS.items())
    return random.choices(tiers, weights=weights, k=1)[0]


def build_description(category: str, tier: str, project: str, location: str) -> str:
    intro = random.choice(INTENSITY_INTRO[tier])
    issue = random.choice(ISSUES[category]).format(project=project, location=location)
    consequence = random.choice(CONSEQUENCE[tier]).format(project=project)
    return f"{intro} risk: {issue}, which {consequence}."


def generate_rows(n: int):
    rows = []
    for i in range(1, n + 1):
        tier = weighted_tier()
        category = random.choice(CATEGORIES)
        project = random.choice(PROJECTS)
        location = random.choice(LOCATIONS)
        sector = random.choice(SECTORS)

        prob_lo, prob_hi = PI_RANGES[tier]["prob"]
        imp_lo, imp_hi = PI_RANGES[tier]["impact"]
        probability = round(random.uniform(prob_lo, prob_hi), 2)
        impact = round(random.uniform(imp_lo, imp_hi), 2)

        severity = severity_from_score(probability, impact)
        description = build_description(category, tier, project, location)

        rows.append({
            "risk_id": f"R{i:04d}",
            "project_id": f"P{((i - 1) % 60) + 1:03d}",
            "sector": sector,
            "location": location,
            "risk_category": category,
            "risk_description": description,
            "probability": probability,
            "impact": impact,
            "severity_label": severity,
        })
    return rows


def main():
    rows = generate_rows(TARGET_ROWS)

    out_path = Path(__file__).resolve().parents[2] / "data" / "processed" / "training_data.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["risk_id", "project_id", "sector", "location", "risk_category",
                   "risk_description", "probability", "impact", "severity_label"]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Quick distribution summary for sanity-checking
    from collections import Counter
    dist = Counter(r["severity_label"] for r in rows)
    cat_dist = Counter(r["risk_category"] for r in rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    print("Severity distribution:", dict(dist))
    print("Category distribution:", dict(cat_dist))


if __name__ == "__main__":
    main()

"""
recommender.py
TF-IDF cosine similarity recommender for I-PRAMRS.
"""

import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KB_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "mitigations.json"

_mitigations = None
_tfidf = None
_matrix = None


def _load_knowledge_base():
    global _mitigations, _tfidf, _matrix
    if _mitigations is not None:
        return
    with open(KB_PATH, "r", encoding="utf-8") as f:
        _mitigations = json.load(f)
    corpus = [m["description"] for m in _mitigations]
    _tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    _matrix = _tfidf.fit_transform(corpus)


def recommend(description: str, risk_category: str, severity: str, top_n: int = 3) -> list:
    """
    Return top-N mitigation strategies for a given risk.
    Ranking: category match first, then severity match, then cosine similarity.
    """
    _load_knowledge_base()
    query_vec = _tfidf.transform([description])
    scores = cosine_similarity(query_vec, _matrix).flatten()

    scored = []
    for i, entry in enumerate(_mitigations):
        scored.append({
            **entry,
            "similarity_score": round(float(scores[i]), 4),
            "_category_match": entry["risk_category"] == risk_category,
            "_severity_match": severity in entry.get("severity_applicability", []),
        })

    scored.sort(
        key=lambda x: (x["_category_match"], x["_severity_match"], x["similarity_score"]),
        reverse=True,
    )
    return [{k: v for k, v in e.items() if not k.startswith("_")} for e in scored[:top_n]]


if __name__ == "__main__":
    tests = [
        ("ZESCO load shedding disrupting server uptime at the Lusaka branch during mobile money integration.", "External/Stakeholder", "High"),
        ("Key developer resigned midway through the e-commerce rollout, leaving a critical knowledge gap.", "Resource/Staffing", "Critical"),
        ("ZMW depreciation pushing imported cloud licence costs beyond the approved budget.", "Cost/Financial", "Medium"),
    ]
    print("recommender.py smoke test\n" + "=" * 55)
    for desc, cat, sev in tests:
        print(f"\nCategory: {cat} | Severity: {sev}")
        print(f"Risk: {desc[:75]}...")
        for i, r in enumerate(recommend(desc, cat, sev), 1):
            print(f"  {i}. [{r['id']}] {r['description'][:85]}")
            print(f"     Score: {r['similarity_score']:.4f} | {r['source']}")

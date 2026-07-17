"""
classifier.py
Inference wrapper for I-PRAMRS severity classifier.
"""

from pathlib import Path
import joblib
import numpy as np
from scipy.sparse import csr_matrix, hstack

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = PROJECT_ROOT / "models_saved"

_model = None
_tfidf = None
_scaler = None


def _load_artifacts():
    global _model, _tfidf, _scaler
    if _model is None:
        _model  = joblib.load(MODELS_DIR / "severity_classifier.pkl")
        _tfidf  = joblib.load(MODELS_DIR / "tfidf_vectorizer.pkl")
        _scaler = joblib.load(MODELS_DIR / "numeric_scaler.pkl")


def classify(description: str, probability: float, impact: float) -> dict:
    """
    Returns: {"severity": str, "confidence": float, "all_probs": dict}
    """
    _load_artifacts()
    text_features = _tfidf.transform([description])
    num_features  = _scaler.transform([[probability, impact]])
    X = hstack([text_features, csr_matrix(num_features)])

    proba   = _model.predict_proba(X)[0]
    classes = _model.classes_
    return {
        "severity":   classes[int(np.argmax(proba))],
        "confidence": round(float(np.max(proba)), 4),
        "all_probs":  {cls: round(float(p), 4) for cls, p in zip(classes, proba)},
    }


if __name__ == "__main__":
    tests = [
        ("Minor compatibility issue with POS hardware, resolved quickly.", 0.10, 0.15, "Low"),
        ("ZESCO load shedding disrupting server uptime at the Lusaka branch.", 0.70, 0.65, "High"),
        ("Critical data loss during database migration threatening the project.", 0.85, 0.90, "Critical"),
        ("ZMW depreciation increasing software licence costs beyond budget.", 0.55, 0.50, "Medium"),
    ]
    print("classifier.py smoke test\n" + "=" * 45)
    for desc, prob, imp, expected in tests:
        r = classify(desc, prob, imp)
        status = "PASS" if r["severity"] == expected else "WARN"
        print(f"[{status}] Expected: {expected:8s} | Got: {r['severity']:8s} | Confidence: {r['confidence']:.2%}")

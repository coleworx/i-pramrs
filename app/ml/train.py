"""
train.py

Trains the I-PRAMRS severity classifier on data/processed/training_data.csv.

Trains three models for comparison (per dissertation methodology):
  - Random Forest (PRIMARY model used by the Flask app)
  - Support Vector Machine (linear kernel, comparison baseline)
  - Logistic Regression (comparison baseline)

Feature pipeline:
  - TF-IDF over `risk_description` (text)
  - StandardScaler over `probability` and `impact` (numeric)
  - Combined via scipy.sparse.hstack

Outputs (used directly in Chapter 4 - Results and Discussion):
  - models_saved/severity_classifier.pkl   (Random Forest - primary)
  - models_saved/svm_classifier.pkl
  - models_saved/logreg_classifier.pkl
  - models_saved/tfidf_vectorizer.pkl
  - models_saved/numeric_scaler.pkl
  - data/evaluation/model_comparison.csv
  - data/evaluation/confusion_matrix_<model>.csv
  - data/evaluation/classification_report_<model>.txt

Run from the project root:
    python -m app.ml.train
"""

import csv
from pathlib import Path

import joblib
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                              confusion_matrix, f1_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer

SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]
RANDOM_STATE = 42

# Resolve paths relative to project root (this file lives in app/ml/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "training_data.csv"
MODELS_DIR = PROJECT_ROOT / "models_saved"
EVAL_DIR = PROJECT_ROOT / "data" / "evaluation"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    required = {"risk_description", "probability", "impact", "severity_label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"training_data.csv is missing required columns: {missing}")
    return df


def build_features(df: pd.DataFrame):
    """Split data, fit TF-IDF + scaler on the training set, transform both sets."""
    X_train_df, X_test_df, y_train, y_test = train_test_split(
        df, df["severity_label"],
        test_size=0.2, random_state=RANDOM_STATE, stratify=df["severity_label"]
    )

    tfidf = TfidfVectorizer(max_features=300, stop_words="english", ngram_range=(1, 2))
    X_train_text = tfidf.fit_transform(X_train_df["risk_description"])
    X_test_text = tfidf.transform(X_test_df["risk_description"])

    scaler = StandardScaler()
    X_train_num = scaler.fit_transform(X_train_df[["probability", "impact"]])
    X_test_num = scaler.transform(X_test_df[["probability", "impact"]])

    X_train = hstack([X_train_text, csr_matrix(X_train_num)]).tocsr()
    X_test = hstack([X_test_text, csr_matrix(X_test_num)]).tocsr()

    return X_train, X_test, y_train, y_test, tfidf, scaler


def get_models():
    return {
        "random_forest": RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE),
        "svm": SVC(kernel="linear", probability=True, random_state=RANDOM_STATE),
        "logreg": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
    }


def evaluate_and_save(name, model, X_test, y_test, eval_dir: Path):
    preds = model.predict(X_test)

    acc = accuracy_score(y_test, preds)
    weighted_f1 = f1_score(y_test, preds, average="weighted", labels=SEVERITY_ORDER)
    macro_f1 = f1_score(y_test, preds, average="macro", labels=SEVERITY_ORDER)

    # Confusion matrix -> CSV
    cm = confusion_matrix(y_test, preds, labels=SEVERITY_ORDER)
    cm_path = eval_dir / f"confusion_matrix_{name}.csv"
    with open(cm_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["actual\\predicted"] + SEVERITY_ORDER)
        for label, row in zip(SEVERITY_ORDER, cm):
            writer.writerow([label] + list(row))

    # Classification report -> TXT
    report = classification_report(y_test, preds, labels=SEVERITY_ORDER, target_names=SEVERITY_ORDER)
    report_path = eval_dir / f"classification_report_{name}.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n=== {name} ===")
    print(f"Accuracy:     {acc:.4f}")
    print(f"Weighted F1:  {weighted_f1:.4f}")
    print(f"Macro F1:     {macro_f1:.4f}")
    print(report)

    return {"model": name, "accuracy": round(acc, 4),
            "weighted_f1": round(weighted_f1, 4), "macro_f1": round(macro_f1, 4)}


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {DATA_PATH} ...")
    df = load_data()
    print(f"Loaded {len(df)} rows.")

    X_train, X_test, y_train, y_test, tfidf, scaler = build_features(df)

    results = []
    trained_models = {}

    for name, model in get_models().items():
        print(f"\nTraining {name} ...")
        model.fit(X_train, y_train)
        trained_models[name] = model
        results.append(evaluate_and_save(name, model, X_test, y_test, EVAL_DIR))

    # --- Gate check: primary model (Random Forest) must exceed 65% weighted F1 ---
    rf_result = next(r for r in results if r["model"] == "random_forest")
    gate_passed = rf_result["weighted_f1"] >= 0.65
    print(f"\n{'='*50}")
    print(f"GATE CHECK (Random Forest weighted F1 >= 0.65): "
          f"{rf_result['weighted_f1']:.4f} -> {'PASS' if gate_passed else 'FAIL'}")
    print(f"{'='*50}")

    # --- Save model comparison table ---
    comparison_path = EVAL_DIR / "model_comparison.csv"
    with open(comparison_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "accuracy", "weighted_f1", "macro_f1"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nModel comparison saved to {comparison_path}")

    # --- Persist artifacts ---
    joblib.dump(trained_models["random_forest"], MODELS_DIR / "severity_classifier.pkl")
    joblib.dump(trained_models["svm"], MODELS_DIR / "svm_classifier.pkl")
    joblib.dump(trained_models["logreg"], MODELS_DIR / "logreg_classifier.pkl")
    joblib.dump(tfidf, MODELS_DIR / "tfidf_vectorizer.pkl")
    joblib.dump(scaler, MODELS_DIR / "numeric_scaler.pkl")
    print(f"Model artifacts saved to {MODELS_DIR}")

    if not gate_passed:
        print("\nWARNING: Gate check failed. Review dataset/feature pipeline before proceeding to Flask work.")


if __name__ == "__main__":
    main()

"""
test_classifier.py
Unit tests for app/ml/classifier.py - the inference wrapper.
"""
import pytest
from app.ml.classifier import classify


class TestClassifier:

    def test_returns_expected_keys(self):
        result = classify("A minor issue with the point-of-sale hardware.", 0.2, 0.2)
        assert set(result.keys()) == {"severity", "confidence", "all_probs"}

    def test_severity_is_valid_label(self):
        result = classify("A minor issue with the point-of-sale hardware.", 0.2, 0.2)
        assert result["severity"] in ["Low", "Medium", "High", "Critical"]

    def test_confidence_in_valid_range(self):
        result = classify("A minor issue with the point-of-sale hardware.", 0.2, 0.2)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_all_probs_sum_to_approximately_one(self):
        result = classify("A minor issue with the point-of-sale hardware.", 0.2, 0.2)
        total = sum(result["all_probs"].values())
        assert abs(total - 1.0) < 0.01

    def test_all_four_classes_present_in_probs(self):
        result = classify("A minor issue with the point-of-sale hardware.", 0.2, 0.2)
        for label in ["Low", "Medium", "High", "Critical"]:
            assert label in result["all_probs"]

    def test_low_probability_low_impact_tends_low_severity(self):
        result = classify(
            "A minor compatibility issue was found and resolved quickly with no disruption.",
            0.05, 0.05
        )
        assert result["severity"] in ["Low", "Medium"]

    def test_high_probability_high_impact_tends_high_severity(self):
        result = classify(
            "A critical, severe risk threatening to halt the entire project immediately.",
            0.9, 0.9
        )
        assert result["severity"] in ["High", "Critical"]

    def test_handles_empty_description_gracefully(self):
        # Should not raise, even with minimal/empty text input
        result = classify("", 0.5, 0.5)
        assert result["severity"] in ["Low", "Medium", "High", "Critical"]

    def test_predicted_class_matches_max_probability(self):
        result = classify("ZESCO load shedding disrupting server uptime.", 0.6, 0.6)
        max_label = max(result["all_probs"], key=result["all_probs"].get)
        assert result["severity"] == max_label

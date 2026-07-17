"""
test_recommender.py
Unit tests for app/ml/recommender.py - the TF-IDF mitigation recommender.
"""
import pytest
from app.ml.recommender import recommend


class TestRecommender:

    def test_returns_requested_number_of_results(self):
        results = recommend(
            "ZESCO load shedding is disrupting server uptime.",
            "External/Stakeholder", "High", top_n=3
        )
        assert len(results) == 3

    def test_returns_fewer_if_top_n_exceeds_available(self):
        results = recommend(
            "A generic risk description.", "Technical", "Low", top_n=100
        )
        assert len(results) <= 100  # should not error, capped at KB size

    def test_result_has_expected_fields(self):
        results = recommend(
            "A currency depreciation risk affecting software costs.",
            "Cost/Financial", "Medium", top_n=1
        )
        expected_fields = {"id", "risk_category", "severity_applicability",
                            "description", "implementation_steps", "source",
                            "similarity_score"}
        assert expected_fields.issubset(results[0].keys())

    def test_category_match_ranked_first(self):
        results = recommend(
            "Staff resigned mid-project causing a knowledge gap.",
            "Resource/Staffing", "Critical", top_n=3
        )
        # At least the top result should match the requested category
        assert results[0]["risk_category"] == "Resource/Staffing"

    def test_similarity_scores_are_valid_range(self):
        results = recommend(
            "A scope creep issue affecting requirements.",
            "Scope/Requirements", "Medium", top_n=5
        )
        for r in results:
            assert 0.0 <= r["similarity_score"] <= 1.0

    def test_all_six_categories_return_results(self):
        categories = ["Technical", "Schedule", "Cost/Financial",
                       "Resource/Staffing", "Scope/Requirements", "External/Stakeholder"]
        for cat in categories:
            results = recommend(f"A generic {cat} risk description.", cat, "Medium", top_n=3)
            assert len(results) == 3
            assert all(r["risk_category"] for r in results)

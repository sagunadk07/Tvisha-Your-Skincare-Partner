import os

import pytest

import recommendation_engine
from model_inference import CLASS_NAMES

FIXTURE_CSV = os.path.join(os.path.dirname(__file__), "fixtures", "test_recommendations.csv")


@pytest.fixture
def use_fixture_csv(monkeypatch):
    """Point get_recommendation() at a small, controlled CSV instead of the real data file,
    so these tests don't break if someone edits real recommendation content."""
    monkeypatch.setattr(recommendation_engine, "CSV_PATH", FIXTURE_CSV)


def test_known_class_returns_full_data(use_fixture_csv):
    result = recommendation_engine.get_recommendation("inflammatory acne")
    assert result["concern_name"] == "Inflammatory Acne"
    assert result["ingredients"] == ["Salicylic Acid", "Benzoyl Peroxide"]
    assert result["suggested_products"] == [
        {"brand": "CeraVe", "name": "Foaming Cleanser"},
        {"brand": "The Ordinary", "name": "Niacinamide"},
    ]
    assert result["skincare_advice"] == ["Wash twice daily", "Avoid picking"]


def test_lookup_is_case_insensitive(use_fixture_csv):
    result = recommendation_engine.get_recommendation("INFLAMMATORY ACNE")
    assert result["concern_name"] == "Inflammatory Acne"


def test_unknown_class_returns_fallback_not_a_crash(use_fixture_csv):
    result = recommendation_engine.get_recommendation("nonexistent condition")
    assert result["concern_name"] == "nonexistent condition"
    assert result["explanation"] == "No recommendation data found for this condition."
    assert result["ingredients"] == []
    assert result["suggested_products"] == []
    assert result["skincare_advice"] == []


def test_parse_product_missing_separator_does_not_crash():
    # partition("::") on a string with no "::" puts everything in `brand`, name stays empty -
    # worth locking in explicitly since a malformed CSV row shouldn't crash the whole page
    result = recommendation_engine._parse_product("JustABrandNoSeparator")
    assert result == {"brand": "JustABrandNoSeparator", "name": ""}


def test_real_csv_has_an_entry_for_every_model_class():
    """Regression guard: the real skin_recommendations.csv and model_inference.CLASS_NAMES
    are two separate files that have no automatic link between them. If someone edits one
    without the other, this is the test that would catch a class silently falling back to
    "No recommendation data found" for real users. Deliberately uses the real CSV_PATH,
    not the fixture above."""
    for class_name in CLASS_NAMES:
        result = recommendation_engine.get_recommendation(class_name)
        assert result["explanation"] != "No recommendation data found for this condition.", (
            f"No recommendation row found for model class '{class_name}' in the real CSV"
        )

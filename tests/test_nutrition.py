"""
Unit tests for nutrition_data.py:
  - calculate_nutrition_totals
  - calculate_deficiencies
  - calculate_personal_rda
  - search_food_local
"""
import pytest
from nutrition_data import (
    calculate_nutrition_totals,
    calculate_deficiencies,
    calculate_personal_rda,
    search_food_local,
    FOOD_DATABASE,
    RDA,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_log(calories=200, protein=20, carbs=25, fat=8,
              fiber=3, omega3=0.1, **extra_nutrition):
    """Build a log dict as stored after JS pre-scaling (quantity=100 → ratio 1)."""
    nutrition = {
        "calories": calories, "protein": protein, "carbs": carbs,
        "fat": fat, "fiber": fiber, "omega3": omega3,
        "sugar": 0, "saturated_fat": 0, "omega6": 0,
        "vitamins": {}, "minerals": {}, "amino_acids": {},
        **extra_nutrition
    }
    return {"quantity": 100, "nutrition": nutrition}


# ══════════════════════════════════════════════════════════════════════════
# calculate_nutrition_totals
# ══════════════════════════════════════════════════════════════════════════

class TestCalculateNutritionTotals:

    def test_empty_list_returns_all_zeros(self):
        totals = calculate_nutrition_totals([])
        assert totals["calories"] == 0
        assert totals["protein"] == 0
        assert totals["carbs"] == 0
        assert totals["fat"] == 0
        assert totals["fiber"] == 0
        assert totals["omega3"] == 0

    def test_empty_list_has_vitamin_keys(self):
        totals = calculate_nutrition_totals([])
        assert "vitamins" in totals
        assert "a" in totals["vitamins"]
        assert "minerals" in totals
        assert "calcium" in totals["minerals"]
        assert "amino_acids" in totals
        assert "leucine" in totals["amino_acids"]

    def test_single_log_calories(self):
        logs = [_make_log(calories=330, protein=62)]
        totals = calculate_nutrition_totals(logs)
        assert totals["calories"] == pytest.approx(330)
        assert totals["protein"] == pytest.approx(62)

    def test_two_logs_sum_calories(self):
        logs = [_make_log(calories=300), _make_log(calories=200)]
        totals = calculate_nutrition_totals(logs)
        assert totals["calories"] == pytest.approx(500)

    def test_no_double_scaling_quantity_100(self):
        """
        Nutrition is pre-scaled before storage; quantity=100 keeps ratio=1.
        Regression test: this was double-scaling (calories × 2) before the fix.
        """
        logs = [{"quantity": 100, "nutrition": {"calories": 330, "protein": 62,
                 "carbs": 0, "fat": 7.2, "fiber": 0, "sugar": 0,
                 "saturated_fat": 0, "omega3": 0.1, "omega6": 0,
                 "vitamins": {}, "minerals": {}, "amino_acids": {}}}]
        totals = calculate_nutrition_totals(logs)
        assert totals["calories"] == pytest.approx(330, abs=0.01)

    def test_vitamins_aggregate_across_logs(self):
        logs = [
            {"quantity": 100, "nutrition": {
                "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0,
                "sugar": 0, "saturated_fat": 0, "omega3": 0, "omega6": 0,
                "vitamins": {"c": 30, "d": 5}, "minerals": {}, "amino_acids": {}
            }},
            {"quantity": 100, "nutrition": {
                "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0,
                "sugar": 0, "saturated_fat": 0, "omega3": 0, "omega6": 0,
                "vitamins": {"c": 20, "d": 10}, "minerals": {}, "amino_acids": {}
            }},
        ]
        totals = calculate_nutrition_totals(logs)
        assert totals["vitamins"]["c"] == pytest.approx(50)
        assert totals["vitamins"]["d"] == pytest.approx(15)

    def test_amino_acids_aggregate(self):
        logs = [
            {"quantity": 100, "nutrition": {
                "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0,
                "sugar": 0, "saturated_fat": 0, "omega3": 0, "omega6": 0,
                "vitamins": {}, "minerals": {},
                "amino_acids": {"leucine": 2.6, "lysine": 2.8}
            }},
            {"quantity": 100, "nutrition": {
                "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0,
                "sugar": 0, "saturated_fat": 0, "omega3": 0, "omega6": 0,
                "vitamins": {}, "minerals": {},
                "amino_acids": {"leucine": 1.0, "lysine": 0.5}
            }},
        ]
        totals = calculate_nutrition_totals(logs)
        assert totals["amino_acids"]["leucine"] == pytest.approx(3.6)
        assert totals["amino_acids"]["lysine"] == pytest.approx(3.3)

    def test_missing_nutrition_keys_default_to_zero(self):
        logs = [{"quantity": 100, "nutrition": {"calories": 100}}]
        totals = calculate_nutrition_totals(logs)
        assert totals["calories"] == pytest.approx(100)
        assert totals["protein"] == 0
        assert totals["fat"] == 0


# ══════════════════════════════════════════════════════════════════════════
# calculate_deficiencies
# ══════════════════════════════════════════════════════════════════════════

class TestCalculateDeficiencies:

    def test_zero_intake_is_zero_percent(self):
        totals = calculate_nutrition_totals([])
        d = calculate_deficiencies(totals)
        assert d["calories"] == 0.0
        assert d["protein"] == 0.0

    def test_full_calorie_intake_is_100_percent(self):
        logs = [_make_log(calories=RDA["calories"])]
        totals = calculate_nutrition_totals(logs)
        d = calculate_deficiencies(totals)
        assert d["calories"] == pytest.approx(100, abs=0.5)

    def test_intake_capped_at_200_percent(self):
        logs = [_make_log(calories=RDA["calories"] * 3)]
        totals = calculate_nutrition_totals(logs)
        d = calculate_deficiencies(totals)
        assert d["calories"] == 200.0

    def test_vitamin_deficiency_percentage(self):
        rda_c = RDA["vitamins"]["c"]
        logs = [{"quantity": 100, "nutrition": {
            "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0,
            "sugar": 0, "saturated_fat": 0, "omega3": 0, "omega6": 0,
            "vitamins": {"c": rda_c / 2}, "minerals": {}, "amino_acids": {}
        }}]
        totals = calculate_nutrition_totals(logs)
        d = calculate_deficiencies(totals, RDA)
        assert d["vitamins"]["c"] == pytest.approx(50, abs=1)

    def test_custom_rda_overrides_default(self):
        custom_rda = {**RDA, "calories": 1000}
        logs = [_make_log(calories=500)]
        totals = calculate_nutrition_totals(logs)
        d = calculate_deficiencies(totals, custom_rda)
        assert d["calories"] == pytest.approx(50, abs=0.5)

    def test_deficiencies_returns_vitamin_and_mineral_keys(self):
        totals = calculate_nutrition_totals([])
        d = calculate_deficiencies(totals)
        assert "vitamins" in d
        assert "minerals" in d
        assert "amino_acids" in d
        assert "a" in d["vitamins"]
        assert "calcium" in d["minerals"]


# ══════════════════════════════════════════════════════════════════════════
# calculate_personal_rda
# ══════════════════════════════════════════════════════════════════════════

class TestCalculatePersonalRda:

    def test_male_maintain_calories_above_1200(self):
        rda = calculate_personal_rda(75, 175, 28, "male", "moderate", "maintain")
        assert rda["calories"] > 1200

    def test_female_maintain_calories_above_1200(self):
        rda = calculate_personal_rda(60, 165, 30, "female", "moderate", "maintain")
        assert rda["calories"] > 1200

    def test_lose_goal_lower_than_maintain(self):
        maintain = calculate_personal_rda(75, 175, 28, "male", "moderate", "maintain")
        lose = calculate_personal_rda(75, 175, 28, "male", "moderate", "lose")
        assert lose["calories"] < maintain["calories"]

    def test_gain_goal_higher_than_maintain(self):
        maintain = calculate_personal_rda(75, 175, 28, "male", "moderate", "maintain")
        gain = calculate_personal_rda(75, 175, 28, "male", "moderate", "gain")
        assert gain["calories"] > maintain["calories"]

    def test_lose_is_500_less_than_tdee(self):
        maintain = calculate_personal_rda(75, 175, 28, "male", "moderate", "maintain")
        lose = calculate_personal_rda(75, 175, 28, "male", "moderate", "lose")
        assert maintain["calories"] - lose["calories"] == pytest.approx(500, abs=1)

    def test_gain_is_300_more_than_tdee(self):
        maintain = calculate_personal_rda(75, 175, 28, "male", "moderate", "maintain")
        gain = calculate_personal_rda(75, 175, 28, "male", "moderate", "gain")
        assert gain["calories"] - maintain["calories"] == pytest.approx(300, abs=1)

    def test_female_iron_is_18mg(self):
        rda = calculate_personal_rda(60, 165, 30, "female", "moderate", "maintain")
        assert rda["minerals"]["iron"] == 18

    def test_male_iron_uses_default(self):
        rda = calculate_personal_rda(75, 175, 28, "male", "moderate", "maintain")
        assert rda["minerals"]["iron"] == RDA["minerals"]["iron"]

    def test_amino_acids_scale_with_weight(self):
        rda_70 = calculate_personal_rda(70, 170, 30, "male", "moderate", "maintain")
        rda_140 = calculate_personal_rda(140, 170, 30, "male", "moderate", "maintain")
        assert rda_140["amino_acids"]["leucine"] == pytest.approx(
            rda_70["amino_acids"]["leucine"] * 2, rel=0.01
        )

    def test_very_active_higher_than_sedentary(self):
        sedentary = calculate_personal_rda(75, 175, 28, "male", "sedentary", "maintain")
        very_active = calculate_personal_rda(75, 175, 28, "male", "very_active", "maintain")
        assert very_active["calories"] > sedentary["calories"]


# ══════════════════════════════════════════════════════════════════════════
# search_food_local
# ══════════════════════════════════════════════════════════════════════════

class TestSearchFoodLocal:

    def test_finds_chicken_by_name(self):
        results = search_food_local("chicken")
        names = [r["name"] for r in results]
        assert any("Chicken" in n for n in names)

    def test_finds_salmon_by_name(self):
        results = search_food_local("salmon")
        assert len(results) >= 1
        assert results[0]["key"] == "salmon"

    def test_alias_match(self):
        # eggs has alias "boiled egg"
        results = search_food_local("boiled egg")
        keys = [r["key"] for r in results]
        assert "eggs" in keys

    def test_partial_match(self):
        results = search_food_local("oat")
        assert len(results) >= 1

    def test_no_match_returns_empty(self):
        results = search_food_local("xyzzy_no_such_food_12345")
        assert results == []

    def test_max_10_results(self):
        results = search_food_local("a")
        assert len(results) <= 10

    def test_result_has_required_keys(self):
        results = search_food_local("salmon")
        r = results[0]
        for key in ("key", "name", "calories", "protein", "carbs", "fat"):
            assert key in r, f"Missing key: {key}"

    def test_case_insensitive(self):
        lower = search_food_local("chicken")
        upper = search_food_local("CHICKEN")
        assert len(lower) == len(upper)

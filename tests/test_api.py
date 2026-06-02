"""
Integration tests for all Flask routes and API endpoints.

AI service calls are mocked so no real ANTHROPIC_API_KEY is needed.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta

from tests.conftest import CHICKEN_200G


# ── AI mock helpers ────────────────────────────────────────────────────────
# Patch ai_service._generate and ai_service._chat directly so tests work
# regardless of which AI backend is in use.

def _patch_generate(text="OK"):
    return patch("ai_service._generate", return_value=text)

def _patch_chat(text="OK"):
    return patch("ai_service._chat", return_value=text)


# ══════════════════════════════════════════════════════════════════════════
# Page routes — all must return HTTP 200
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("route", [
    "/", "/log", "/chat", "/recipes", "/mindfulness",
    "/profile", "/progress", "/planner", "/grocery",
])
def test_all_pages_return_200(client, route):
    r = client.get(route)
    assert r.status_code == 200, f"{route} returned {r.status_code}"


def test_onboarding_page_returns_200(client):
    r = client.get("/onboarding")
    assert r.status_code == 200


def test_dashboard_does_not_redirect_when_onboarding_complete(client):
    """Profile has onboarding_complete=True; / must render the dashboard."""
    r = client.get("/")
    assert r.status_code == 200
    assert b"Chef" in r.data or b"Dashboard" in r.data


# ══════════════════════════════════════════════════════════════════════════
# Food search
# ══════════════════════════════════════════════════════════════════════════

class TestFoodSearch:

    def test_short_query_returns_empty(self, client):
        r = client.get("/api/food/search?q=a")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_blank_query_returns_empty(self, client):
        r = client.get("/api/food/search?q=")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_finds_chicken(self, client):
        r = client.get("/api/food/search?q=chicken")
        data = r.get_json()
        assert r.status_code == 200
        assert len(data) >= 1
        assert any("Chicken" in item["name"] for item in data)

    def test_result_has_required_fields(self, client):
        r = client.get("/api/food/search?q=salmon")
        data = r.get_json()
        assert len(data) >= 1
        for field in ("key", "name", "calories", "protein", "carbs", "fat"):
            assert field in data[0], f"Missing field: {field}"

    def test_max_10_results(self, client):
        r = client.get("/api/food/search?q=a")
        assert len(r.get_json()) <= 10


# ══════════════════════════════════════════════════════════════════════════
# Food detail
# ══════════════════════════════════════════════════════════════════════════

class TestFoodDetail:

    def test_local_food_returns_nutrition(self, client):
        r = client.get("/api/food/detail?key=chicken_breast")
        assert r.status_code == 200
        data = r.get_json()
        assert "nutrition" in data
        assert data["nutrition"]["calories"] == pytest.approx(165, abs=1)
        assert data["nutrition"]["protein"] == pytest.approx(31.0, abs=0.1)

    def test_local_food_has_vitamins_and_minerals(self, client):
        r = client.get("/api/food/detail?key=salmon")
        data = r.get_json()
        assert "vitamins" in data["nutrition"]
        assert "minerals" in data["nutrition"]
        assert "amino_acids" in data["nutrition"]

    def test_unknown_key_returns_404(self, client):
        r = client.get("/api/food/detail?key=nonexistent_food_xyz")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════
# Food log CRUD
# ══════════════════════════════════════════════════════════════════════════

class TestFoodLog:

    def test_log_food_returns_success(self, client):
        r = client.post("/api/food/log", json=CHICKEN_200G)
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert "id" in data

    def test_log_food_persists(self, client):
        client.post("/api/food/log", json=CHICKEN_200G)
        r = client.get("/api/nutrition/today")
        data = r.get_json()
        assert data["totals"]["calories"] > 0

    def test_no_double_scaling(self, client):
        """
        Regression: pre-scaled nutrition (330 kcal for 200g) must appear
        as 330 kcal in totals, not 660 kcal.
        """
        client.post("/api/food/log", json=CHICKEN_200G)
        r = client.get("/api/nutrition/today")
        totals = r.get_json()["totals"]
        assert totals["calories"] == pytest.approx(330, abs=1)
        assert totals["protein"] == pytest.approx(62.0, abs=0.1)

    def test_two_logs_sum_correctly(self, client):
        client.post("/api/food/log", json=CHICKEN_200G)
        salmon = {**CHICKEN_200G, "food_name": "Salmon", "food_key": "salmon",
                  "nutrition": {**CHICKEN_200G["nutrition"], "calories": 206, "protein": 28.8}}
        client.post("/api/food/log", json=salmon)
        r = client.get("/api/nutrition/today")
        totals = r.get_json()["totals"]
        assert totals["calories"] == pytest.approx(536, abs=2)

    def test_delete_food_log(self, client, one_food_log):
        r = client.delete(f"/api/food/log/{one_food_log}")
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_delete_removes_from_totals(self, client, one_food_log):
        client.delete(f"/api/food/log/{one_food_log}")
        r = client.get("/api/nutrition/today")
        assert r.get_json()["totals"]["calories"] == 0

    def test_delete_nonexistent_returns_404(self, client):
        r = client.delete("/api/food/log/99999")
        assert r.status_code == 404

    def test_log_food_page_renders_with_entries(self, client):
        """Regression: food_log.html was crashing (meal total sum bug)."""
        client.post("/api/food/log", json=CHICKEN_200G)
        r = client.get("/log")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# Nutrition today
# ══════════════════════════════════════════════════════════════════════════

class TestNutritionToday:

    def test_empty_day_returns_zeros(self, client):
        r = client.get("/api/nutrition/today")
        assert r.status_code == 200
        data = r.get_json()
        assert data["totals"]["calories"] == 0
        assert data["totals"]["protein"] == 0

    def test_response_has_rda_and_deficiencies(self, client):
        r = client.get("/api/nutrition/today")
        data = r.get_json()
        assert "rda" in data
        assert "deficiencies" in data
        assert data["rda"]["calories"] > 0

    def test_rda_calculated_from_profile(self, client):
        r = client.get("/api/nutrition/today")
        rda = r.get_json()["rda"]
        # moderate male 75kg 175cm 28y maintain ≈ 2600 kcal
        assert 1800 < rda["calories"] < 3500

    def test_deficiencies_structure(self, client):
        r = client.get("/api/nutrition/today")
        d = r.get_json()["deficiencies"]
        assert "vitamins" in d
        assert "minerals" in d
        assert "amino_acids" in d


# ══════════════════════════════════════════════════════════════════════════
# Calendar data
# ══════════════════════════════════════════════════════════════════════════

class TestCalendar:

    def test_returns_dict_of_date_strings(self, client):
        r = client.get("/api/calendar")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_today_is_in_calendar(self, client):
        r = client.get("/api/calendar")
        data = r.get_json()
        assert str(date.today()) in data

    def test_day_entry_has_required_fields(self, client):
        r = client.get("/api/calendar")
        today_entry = r.get_json()[str(date.today())]
        for field in ("cal_pct", "protein_pct", "mind_pct", "has_data", "calories"):
            assert field in today_entry

    def test_empty_day_has_data_false(self, client):
        r = client.get("/api/calendar")
        today_entry = r.get_json()[str(date.today())]
        assert today_entry["has_data"] is False

    def test_logged_day_has_data_true(self, client):
        client.post("/api/food/log", json=CHICKEN_200G)
        r = client.get("/api/calendar")
        today_entry = r.get_json()[str(date.today())]
        assert today_entry["has_data"] is True
        assert today_entry["calories"] == pytest.approx(330, abs=2)


# ══════════════════════════════════════════════════════════════════════════
# Progress history
# ══════════════════════════════════════════════════════════════════════════

class TestProgressHistory:

    def test_default_30_days(self, client):
        r = client.get("/api/progress/history")
        data = r.get_json()
        assert len(data["history"]) == 30

    def test_custom_days_param(self, client):
        r = client.get("/api/progress/history?days=7")
        data = r.get_json()
        assert len(data["history"]) == 7

    def test_response_has_rda(self, client):
        r = client.get("/api/progress/history")
        assert "rda" in r.get_json()

    def test_each_day_has_required_fields(self, client):
        r = client.get("/api/progress/history?days=3")
        history = r.get_json()["history"]
        for day in history:
            for field in ("date", "calories", "protein", "carbs", "fat",
                          "water_ml", "has_data"):
                assert field in day

    def test_today_calories_after_logging(self, client):
        client.post("/api/food/log", json=CHICKEN_200G)
        r = client.get("/api/progress/history?days=1")
        today = r.get_json()["history"][0]
        assert today["calories"] == pytest.approx(330, abs=2)


# ══════════════════════════════════════════════════════════════════════════
# Streak
# ══════════════════════════════════════════════════════════════════════════

class TestStreak:

    def test_no_logs_streak_is_zero(self, client):
        r = client.get("/api/streak")
        assert r.status_code == 200
        assert r.get_json()["streak"] == 0

    def test_logging_today_gives_streak_1(self, client):
        client.post("/api/food/log", json=CHICKEN_200G)
        r = client.get("/api/streak")
        assert r.get_json()["streak"] == 1


# ══════════════════════════════════════════════════════════════════════════
# Water log
# ══════════════════════════════════════════════════════════════════════════

class TestWaterLog:

    def test_log_water_returns_success(self, client):
        r = client.post("/api/water/log", json={"amount_ml": 500})
        assert r.status_code == 200
        data = r.get_json()
        assert data["success"] is True
        assert "total_ml" in data
        assert "pct" in data

    def test_log_water_accumulates(self, client):
        client.post("/api/water/log", json={"amount_ml": 500})
        client.post("/api/water/log", json={"amount_ml": 300})
        r = client.get("/api/water/today")
        assert r.get_json()["total_ml"] == 800

    def test_water_today_structure(self, client):
        r = client.get("/api/water/today")
        assert r.status_code == 200
        data = r.get_json()
        for field in ("total_ml", "goal_ml", "pct", "logs"):
            assert field in data

    def test_water_pct_correct(self, client):
        client.post("/api/water/log", json={"amount_ml": 1250})
        r = client.get("/api/water/today")
        data = r.get_json()
        assert data["pct"] == pytest.approx(50.0, abs=1)

    def test_water_pct_capped_at_100(self, client):
        client.post("/api/water/log", json={"amount_ml": 10000})
        r = client.get("/api/water/today")
        assert r.get_json()["pct"] == pytest.approx(100.0, abs=0.1)

    def test_delete_water_log(self, client):
        log_id = client.post("/api/water/log", json={"amount_ml": 250}).get_json()["id"]
        r = client.delete(f"/api/water/log/{log_id}")
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_delete_water_log_reduces_total(self, client):
        log_id = client.post("/api/water/log", json={"amount_ml": 500}).get_json()["id"]
        client.post("/api/water/log", json={"amount_ml": 250})
        client.delete(f"/api/water/log/{log_id}")
        r = client.get("/api/water/today")
        assert r.get_json()["total_ml"] == 250


# ══════════════════════════════════════════════════════════════════════════
# Weight log
# ══════════════════════════════════════════════════════════════════════════

class TestWeightLog:

    def test_log_weight_returns_success(self, client):
        r = client.post("/api/weight/log", json={"weight_kg": 74.5})
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_log_weight_updates_profile(self, client):
        client.post("/api/weight/log", json={"weight_kg": 74.0})
        r = client.get("/api/profile")
        assert r.get_json()["weight_kg"] == pytest.approx(74.0)

    def test_log_weight_upserts_today(self, client):
        client.post("/api/weight/log", json={"weight_kg": 74.0})
        client.post("/api/weight/log", json={"weight_kg": 73.5})
        r = client.get("/api/weight/history")
        today_entries = [e for e in r.get_json() if e["date"] == str(date.today())]
        assert len(today_entries) == 1
        assert today_entries[0]["weight_kg"] == pytest.approx(73.5)

    def test_weight_history_returns_list(self, client):
        client.post("/api/weight/log", json={"weight_kg": 75.0})
        r = client.get("/api/weight/history")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)


# ══════════════════════════════════════════════════════════════════════════
# Profile
# ══════════════════════════════════════════════════════════════════════════

class TestProfile:

    def test_get_profile_returns_fields(self, client):
        r = client.get("/api/profile")
        assert r.status_code == 200
        data = r.get_json()
        for field in ("name", "age", "gender", "weight_kg", "height_cm",
                      "activity_level", "goal", "dietary_preference",
                      "water_goal_ml", "custom_calories"):
            assert field in data, f"Missing field: {field}"

    def test_update_name(self, client):
        client.post("/api/profile", json={"name": "Updated Name"})
        r = client.get("/api/profile")
        assert r.get_json()["name"] == "Updated Name"
        # restore
        client.post("/api/profile", json={"name": "Test User"})

    def test_update_water_goal(self, client):
        client.post("/api/profile", json={"water_goal_ml": 3000})
        r = client.get("/api/profile")
        assert r.get_json()["water_goal_ml"] == 3000
        client.post("/api/profile", json={"water_goal_ml": 2500})

    def test_update_custom_calories(self, client):
        client.post("/api/profile", json={"custom_calories": 1800})
        r = client.get("/api/profile")
        assert r.get_json()["custom_calories"] == 1800
        client.post("/api/profile", json={"custom_calories": 0})

    def test_custom_calories_overrides_rda(self, client):
        """When custom_calories is set, nutrition today must use that target."""
        client.post("/api/profile", json={"custom_calories": 1600})
        r = client.get("/api/nutrition/today")
        rda_cal = r.get_json()["rda"]["calories"]
        assert rda_cal == 1600
        client.post("/api/profile", json={"custom_calories": 0})

    def test_update_goal(self, client):
        client.post("/api/profile", json={"goal": "lose"})
        r = client.get("/api/profile")
        assert r.get_json()["goal"] == "lose"
        client.post("/api/profile", json={"goal": "maintain"})

    def test_post_profile_returns_success(self, client):
        r = client.post("/api/profile", json={"allergies": "peanuts"})
        assert r.status_code == 200
        assert r.get_json()["success"] is True
        client.post("/api/profile", json={"allergies": ""})


# ══════════════════════════════════════════════════════════════════════════
# Mindfulness log
# ══════════════════════════════════════════════════════════════════════════

class TestMindfulnessLog:

    def test_log_mindfulness_returns_success(self, client):
        r = client.post("/api/mindfulness/log", json={
            "activity_type": "meditation",
            "duration_minutes": 15,
            "mood_before": 4,
            "mood_after": 8
        })
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_log_mindfulness_has_id(self, client):
        r = client.post("/api/mindfulness/log", json={
            "activity_type": "yoga",
            "duration_minutes": 30
        })
        assert "id" in r.get_json()

    def test_delete_mindfulness_log(self, client):
        log_id = client.post("/api/mindfulness/log", json={
            "activity_type": "breathing", "duration_minutes": 10
        }).get_json()["id"]
        r = client.delete(f"/api/mindfulness/log/{log_id}")
        assert r.status_code == 200
        assert r.get_json()["success"] is True

    def test_delete_nonexistent_mindfulness_returns_404(self, client):
        r = client.delete("/api/mindfulness/log/99999")
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════
# CSV export
# ══════════════════════════════════════════════════════════════════════════

class TestCsvExport:

    def test_export_returns_csv_content_type(self, client):
        r = client.get("/api/export/csv")
        assert r.status_code == 200
        assert "text/csv" in r.content_type

    def test_export_has_header_row(self, client):
        r = client.get("/api/export/csv")
        first_line = r.data.decode().splitlines()[0]
        assert "Date" in first_line
        assert "Calories" in first_line
        assert "Protein" in first_line

    def test_export_includes_logged_food(self, client):
        client.post("/api/food/log", json=CHICKEN_200G)
        r = client.get("/api/export/csv")
        content = r.data.decode()
        assert "Chicken Breast" in content

    def test_export_respects_days_param(self, client):
        r = client.get("/api/export/csv?days=7")
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# AI endpoints — all mocked so no real API key needed
# ══════════════════════════════════════════════════════════════════════════

class TestAIEndpoints:

    def test_daily_insight_returns_insight(self, client):
        with _patch_generate("Eat more greens today!"):
            r = client.get("/api/insight")
        assert r.status_code == 200
        assert "insight" in r.get_json()
        assert len(r.get_json()["insight"]) > 0

    def test_chat_returns_reply(self, client):
        with _patch_chat("Great question about nutrition!"):
            r = client.post("/api/chat", json={"message": "What should I eat?", "category": "nutrition"})
        assert r.status_code == 200
        data = r.get_json()
        assert "reply" in data
        assert data["reply"] == "Great question about nutrition!"

    def test_chat_empty_message_returns_400(self, client):
        r = client.post("/api/chat", json={"message": "  ", "category": "general"})
        assert r.status_code == 400

    def test_recipe_suggest_returns_json(self, client):
        recipe_json = json.dumps({
            "recipes": [{
                "name": "Grilled Chicken", "emoji": "🍗", "time": "20 min",
                "difficulty": "Easy", "nutrients_addressed": ["Protein"],
                "description": "Lean protein", "ingredients": ["200g chicken"],
                "steps": ["Grill it"], "nutrition_per_serving": {"calories": 330},
                "chef_tip": "Season well"
            }]
        })
        with _patch_generate(recipe_json):
            r = client.post("/api/recipes/suggest", json={"preferences": "high protein"})
        assert r.status_code == 200
        data = r.get_json()
        assert "recipes" in data
        assert len(data["recipes"]) == 1

    def test_weekly_report_returns_text(self, client):
        with _patch_generate("## Week at a Glance\nGreat week!"):
            r = client.get("/api/weekly-report")
        assert r.status_code == 200
        assert "report" in r.get_json()

    def test_grocery_generate_returns_categories(self, client):
        grocery_json = json.dumps({
            "total_estimated_cost": "$60-80",
            "categories": [{
                "name": "Proteins", "emoji": "🥩",
                "items": [{"name": "Chicken", "amount": "1kg",
                           "reason": "High protein", "priority": "high"}]
            }]
        })
        with _patch_generate(grocery_json):
            r = client.post("/api/grocery/generate", json={"preferences": ""})
        assert r.status_code == 200
        data = r.get_json()
        assert "categories" in data
        assert len(data["categories"]) >= 1

    def test_meal_plan_generate_returns_days(self, client):
        plan_json = json.dumps({
            "plan_summary": "Balanced 3-day plan",
            "daily_targets": {"calories": 2000, "protein": 150},
            "days": [{
                "day": "Day 1", "nutrition_highlight": "High protein",
                "daily_total": {"calories": 2000, "protein": 150},
                "meals": {
                    "breakfast": {"name": "Oats", "description": "Warm oats",
                                  "calories": 350, "protein": 12, "prep_time": "5 min"},
                    "lunch": {"name": "Chicken Rice", "description": "Lean lunch",
                              "calories": 550, "protein": 45, "prep_time": "15 min"},
                    "dinner": {"name": "Salmon", "description": "Omega-3 rich",
                               "calories": 600, "protein": 50, "prep_time": "20 min"},
                    "snack": {"name": "Greek Yogurt", "description": "Protein snack",
                              "calories": 150, "protein": 15, "prep_time": "1 min"}
                }
            }]
        })
        with _patch_generate(plan_json):
            r = client.post("/api/meal-plan/generate", json={"days": 3, "preferences": ""})
        assert r.status_code == 200
        data = r.get_json()
        assert "days" in data
        assert len(data["days"]) >= 1

    def test_meal_analyze_returns_analysis(self, client):
        with _patch_generate("Nutritious meal with good protein content."):
            r = client.post("/api/meal/analyze", json={
                "food_name": "Chicken Salad",
                "ingredients": "lettuce, chicken, olive oil"
            })
        assert r.status_code == 200
        assert "analysis" in r.get_json()

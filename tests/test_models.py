"""
Tests for SQLAlchemy models:  UserProfile, FoodLog, WaterLog, WeightLog,
MindfulnessLog, ChatMessage.
"""
import json
import pytest
from datetime import date

from database import db as _db
from models import (
    UserProfile, FoodLog, WaterLog, WeightLog, MindfulnessLog, ChatMessage
)


# ══════════════════════════════════════════════════════════════════════════
# UserProfile
# ══════════════════════════════════════════════════════════════════════════

class TestUserProfile:

    def test_profile_exists_in_db(self, app, _db_session):
        with app.app_context():
            profile = UserProfile.query.first()
            assert profile is not None

    def test_profile_has_correct_test_values(self, app, _db_session):
        with app.app_context():
            p = UserProfile.query.first()
            assert p.name == "Test User"
            assert p.age == 28
            assert p.gender == "male"
            assert p.weight_kg == pytest.approx(75.0)
            assert p.height_cm == pytest.approx(175.0)
            assert p.onboarding_complete is True

    def test_profile_water_goal_default(self, app, _db_session):
        with app.app_context():
            p = UserProfile.query.first()
            assert p.water_goal_ml == 2500

    def test_profile_custom_targets_default_zero(self, app, _db_session):
        with app.app_context():
            p = UserProfile.query.first()
            assert p.custom_calories == 0
            assert p.custom_protein == 0
            assert p.custom_carbs == 0
            assert p.custom_fat == 0

    def test_profile_onboarding_flag(self, app, _db_session):
        with app.app_context():
            p = UserProfile.query.first()
            assert isinstance(p.onboarding_complete, (bool, int))


# ══════════════════════════════════════════════════════════════════════════
# FoodLog — nutrition JSON property
# ══════════════════════════════════════════════════════════════════════════

class TestFoodLog:

    def test_nutrition_setter_and_getter(self, app, _db_session):
        nutrition = {
            "calories": 165, "protein": 31.0, "carbs": 0.0,
            "fat": 3.6, "vitamins": {"b3": 12.5}, "minerals": {}, "amino_acids": {}
        }
        with app.app_context():
            log = FoodLog(
                date=date.today(),
                meal_type="lunch",
                food_name="Chicken Breast",
                food_key="chicken_breast",
                quantity_g=100.0
            )
            log.nutrition = nutrition
            _db.session.add(log)
            _db.session.commit()

            fetched = FoodLog.query.get(log.id)
            assert fetched.nutrition["calories"] == 165
            assert fetched.nutrition["protein"] == pytest.approx(31.0)
            assert fetched.nutrition["vitamins"]["b3"] == pytest.approx(12.5)

    def test_nutrition_json_is_stored_as_text(self, app, _db_session):
        with app.app_context():
            log = FoodLog(
                date=date.today(), meal_type="snack",
                food_name="Apple", quantity_g=150.0
            )
            log.nutrition = {"calories": 78, "protein": 0.4}
            _db.session.add(log)
            _db.session.commit()

            # The raw column should be valid JSON text
            raw = FoodLog.query.get(log.id).nutrition_json
            parsed = json.loads(raw)
            assert parsed["calories"] == 78

    def test_food_log_date_defaults_to_today(self, app, _db_session):
        with app.app_context():
            log = FoodLog(food_name="Test", quantity_g=100)
            log.nutrition = {}
            _db.session.add(log)
            _db.session.commit()
            assert FoodLog.query.get(log.id).date == date.today()

    def test_food_log_meal_type_default(self, app, _db_session):
        with app.app_context():
            log = FoodLog(food_name="Test", quantity_g=100)
            log.nutrition = {}
            _db.session.add(log)
            _db.session.commit()
            assert FoodLog.query.get(log.id).meal_type == "lunch"

    def test_multiple_logs_independent(self, app, _db_session):
        """Two FoodLog rows store independent nutrition JSON blobs."""
        with app.app_context():
            a = FoodLog(food_name="A", quantity_g=100, meal_type="breakfast")
            a.nutrition = {"calories": 100}
            b = FoodLog(food_name="B", quantity_g=200, meal_type="dinner")
            b.nutrition = {"calories": 400}
            _db.session.add_all([a, b])
            _db.session.commit()

            assert FoodLog.query.get(a.id).nutrition["calories"] == 100
            assert FoodLog.query.get(b.id).nutrition["calories"] == 400


# ══════════════════════════════════════════════════════════════════════════
# WaterLog
# ══════════════════════════════════════════════════════════════════════════

class TestWaterLog:

    def test_water_log_stores_amount(self, app, _db_session):
        with app.app_context():
            log = WaterLog(date=date.today(), amount_ml=500)
            _db.session.add(log)
            _db.session.commit()
            assert WaterLog.query.get(log.id).amount_ml == 500

    def test_water_log_date_defaults_to_today(self, app, _db_session):
        with app.app_context():
            log = WaterLog(amount_ml=250)
            _db.session.add(log)
            _db.session.commit()
            assert WaterLog.query.get(log.id).date == date.today()


# ══════════════════════════════════════════════════════════════════════════
# WeightLog
# ══════════════════════════════════════════════════════════════════════════

class TestWeightLog:

    def test_weight_log_stores_value(self, app, _db_session):
        with app.app_context():
            log = WeightLog(date=date.today(), weight_kg=74.5, notes="morning")
            _db.session.add(log)
            _db.session.commit()
            fetched = WeightLog.query.get(log.id)
            assert fetched.weight_kg == pytest.approx(74.5)
            assert fetched.notes == "morning"


# ══════════════════════════════════════════════════════════════════════════
# MindfulnessLog
# ══════════════════════════════════════════════════════════════════════════

class TestMindfulnessLog:

    def test_mindfulness_log_fields(self, app, _db_session):
        with app.app_context():
            log = MindfulnessLog(
                date=date.today(),
                activity_type="meditation",
                duration_minutes=15,
                notes="calm session",
                mood_before=4,
                mood_after=8
            )
            _db.session.add(log)
            _db.session.commit()
            fetched = MindfulnessLog.query.get(log.id)
            assert fetched.activity_type == "meditation"
            assert fetched.duration_minutes == 15
            assert fetched.mood_before == 4
            assert fetched.mood_after == 8


# ══════════════════════════════════════════════════════════════════════════
# ChatMessage
# ══════════════════════════════════════════════════════════════════════════

class TestChatMessage:

    def test_chat_message_stores_role_and_content(self, app, _db_session):
        with app.app_context():
            msg = ChatMessage(role="user", content="Hello NutriAI", category="nutrition")
            _db.session.add(msg)
            _db.session.commit()
            fetched = ChatMessage.query.get(msg.id)
            assert fetched.role == "user"
            assert fetched.content == "Hello NutriAI"
            assert fetched.category == "nutrition"

    def test_chat_message_default_category(self, app, _db_session):
        with app.app_context():
            msg = ChatMessage(role="assistant", content="Hi!")
            _db.session.add(msg)
            _db.session.commit()
            assert ChatMessage.query.get(msg.id).category == "general"

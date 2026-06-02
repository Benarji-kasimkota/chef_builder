"""
Shared fixtures for the Chef Builder test suite.

DATABASE_URL must be set before app.py is imported so that load_dotenv()
(which doesn't override existing env vars) picks up our test database
instead of the production one.
"""
import os
import sys

# ── Override env vars BEFORE any app imports ───────────────────────────────
os.environ["DATABASE_URL"] = "sqlite:////tmp/test_chefbuilder.db"
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-placeholder")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app import app as flask_app
from database import db as _db
from models import (
    UserProfile, FoodLog, WaterLog, WeightLog, MindfulnessLog, ChatMessage
)

# ── Sample pre-scaled nutrition payload (200 g chicken breast) ─────────────
CHICKEN_200G = {
    "food_name": "Chicken Breast (cooked)",
    "food_key": "chicken_breast",
    "quantity_g": 200,
    "meal_type": "lunch",
    "nutrition": {
        "calories": 330.0, "protein": 62.0, "carbs": 0.0,
        "fat": 7.2, "fiber": 0.0, "sugar": 0.0,
        "saturated_fat": 2.0, "omega3": 0.10, "omega6": 1.40,
        "vitamins": {"b3": 25.0, "b6": 1.6, "d": 0.2},
        "minerals": {"phosphorus": 440, "potassium": 512, "selenium": 48},
        "amino_acids": {"leucine": 5.2, "lysine": 5.6, "isoleucine": 3.2}
    }
}


# ── Session-scoped: build the test DB once ─────────────────────────────────
@pytest.fixture(scope="session")
def app():
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    return flask_app


@pytest.fixture(scope="session")
def _db_session(app):
    """
    Ensure the test DB has a fully-configured profile so the dashboard
    renders without redirecting to onboarding.
    """
    with app.app_context():
        _db.create_all()
        profile = UserProfile.query.first()
        if not profile:
            profile = UserProfile()
            _db.session.add(profile)
            _db.session.commit()
        # Patch the default profile to be onboarding-complete
        profile.name = "Test User"
        profile.age = 28
        profile.gender = "male"
        profile.weight_kg = 75.0
        profile.height_cm = 175.0
        profile.activity_level = "moderate"
        profile.goal = "maintain"
        profile.dietary_preference = "omnivore"
        profile.water_goal_ml = 2500
        profile.onboarding_complete = True
        _db.session.commit()

    yield

    # tear-down: remove the temp DB file
    try:
        os.unlink("/tmp/test_chefbuilder.db")
    except FileNotFoundError:
        pass


# ── Function-scoped: fresh client + clean log tables per test ──────────────
@pytest.fixture()
def client(app, _db_session):
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clean_logs(app, _db_session):
    """Delete all transient rows after every test; keep the profile intact."""
    yield
    with app.app_context():
        FoodLog.query.delete()
        WaterLog.query.delete()
        WeightLog.query.delete()
        MindfulnessLog.query.delete()
        ChatMessage.query.delete()
        _db.session.commit()


# ── Helper fixture: one food log entry already in the DB ───────────────────
@pytest.fixture()
def one_food_log(client):
    r = client.post("/api/food/log", json=CHICKEN_200G)
    return r.get_json()["id"]

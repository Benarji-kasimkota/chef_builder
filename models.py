from datetime import datetime, date
from database import db
import json


class UserProfile(db.Model):
    __tablename__ = "user_profile"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="User")
    age = db.Column(db.Integer, default=30)
    gender = db.Column(db.String(10), default="male")
    weight_kg = db.Column(db.Float, default=70.0)
    height_cm = db.Column(db.Float, default=170.0)
    activity_level = db.Column(db.String(20), default="moderate")
    goal = db.Column(db.String(20), default="maintain")
    dietary_preference = db.Column(db.String(30), default="omnivore")
    allergies = db.Column(db.Text, default="")
    # Custom macro targets (0 = use auto-calculated RDA)
    custom_calories = db.Column(db.Integer, default=0)
    custom_protein = db.Column(db.Integer, default=0)
    custom_carbs = db.Column(db.Integer, default=0)
    custom_fat = db.Column(db.Integer, default=0)
    # Water goal in ml
    water_goal_ml = db.Column(db.Integer, default=2500)
    # Onboarding
    onboarding_complete = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FoodLog(db.Model):
    __tablename__ = "food_log"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    meal_type = db.Column(db.String(20), default="lunch")
    food_name = db.Column(db.String(200), nullable=False)
    food_key = db.Column(db.String(100))
    quantity_g = db.Column(db.Float, default=100.0)
    nutrition_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def nutrition(self):
        return json.loads(self.nutrition_json)

    @nutrition.setter
    def nutrition(self, value):
        self.nutrition_json = json.dumps(value)


class MindfulnessLog(db.Model):
    __tablename__ = "mindfulness_log"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    activity_type = db.Column(db.String(50))
    duration_minutes = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text, default="")
    mood_before = db.Column(db.Integer, default=5)
    mood_after = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WeightLog(db.Model):
    __tablename__ = "weight_log"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    weight_kg = db.Column(db.Float)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class WaterLog(db.Model):
    __tablename__ = "water_log"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    amount_ml = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatMessage(db.Model):
    __tablename__ = "chat_message"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(10))
    content = db.Column(db.Text)
    category = db.Column(db.String(30), default="general")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

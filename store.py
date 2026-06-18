"""
Unified database layer.

Set FIREBASE_CREDENTIALS (minified JSON of a Firebase service-account key) to
use Firestore. Without it the app falls back to SQLAlchemy + SQLite — the same
path used by local development and the test suite, so tests need no changes.

Firestore note: queries that combine a date-equality filter with ordering by
created_at require a composite index. Firestore will print a link to create it
on first run. Alternatively, ordering is done in Python here for those queries.
"""

import os
import json
from datetime import date, datetime, timedelta

_USE_FIREBASE = bool(os.environ.get("FIREBASE_CREDENTIALS"))

# Vercel's filesystem is ephemeral — SQLite data is wiped on every redeploy.
# Fail loudly rather than silently losing all user data.
if not _USE_FIREBASE and os.environ.get("VERCEL"):
    raise RuntimeError(
        "FIREBASE_CREDENTIALS is not set but the app is running on Vercel, where the "
        "filesystem is ephemeral. All SQLite data would be lost on every redeploy. "
        "Add FIREBASE_CREDENTIALS (your Firebase service-account JSON, minified) to "
        "the Vercel dashboard environment variables and redeploy."
    )


class _Row:
    """Attribute-access wrapper — gives Firestore dicts the same .field syntax
    that SQLAlchemy model instances provide."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


# ─────────────────────────────────────────────────────────────────────────────
#  Firestore backend
# ─────────────────────────────────────────────────────────────────────────────
if _USE_FIREBASE:
    import firebase_admin
    from firebase_admin import credentials, firestore as _fs

    _client_cache = None

    def _db():
        global _client_cache
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(os.environ["FIREBASE_CREDENTIALS"]))
            firebase_admin.initialize_app(cred)
        if _client_cache is None:
            _client_cache = _fs.client()
        return _client_cache

    def init_store(app):
        _db()  # initialise eagerly so startup errors surface immediately

    # ── Profile ────────────────────────────────────────────────────────────────

    _PROFILE_DEFAULTS = dict(
        name="User", age=30, gender="male", weight_kg=70.0, height_cm=170.0,
        activity_level="moderate", goal="maintain", dietary_preference="omnivore",
        allergies="", custom_calories=0, custom_protein=0, custom_carbs=0,
        custom_fat=0, water_goal_ml=2500, onboarding_complete=False,
    )

    def get_profile():
        ref = _db().collection("user_profile").document("singleton")
        doc = ref.get()
        if not doc.exists:
            ref.set(_PROFILE_DEFAULTS)
            return _Row(**_PROFILE_DEFAULTS)
        return _Row(**{**_PROFILE_DEFAULTS, **doc.to_dict()})

    def save_profile(updates):
        _db().collection("user_profile").document("singleton").set(updates, merge=True)

    # ── Food logs ──────────────────────────────────────────────────────────────

    def _food_row(doc):
        d = doc.to_dict()
        nutrition = d.get("nutrition", {})
        ts = d.get("created_at", datetime.utcnow().isoformat())
        return _Row(
            id=doc.id,
            date=date.fromisoformat(d["date"]),
            meal_type=d.get("meal_type", "lunch"),
            food_name=d.get("food_name", ""),
            food_key=d.get("food_key", ""),
            quantity_g=d.get("quantity_g", 100.0),
            nutrition=nutrition,
            nutrition_json=json.dumps(nutrition),
            created_at=ts,
        )

    def get_today_logs():
        docs = list(_db().collection("food_logs")
                    .where("date", "==", str(date.today())).stream())
        return sorted([_food_row(d) for d in docs], key=lambda x: x.created_at)

    def get_food_logs_for_date(target_date):
        docs = list(_db().collection("food_logs")
                    .where("date", "==", str(target_date)).stream())
        return [_food_row(d) for d in docs]

    def get_food_logs_range(start_date, end_date):
        docs = list(_db().collection("food_logs")
                    .where("date", ">=", str(start_date))
                    .where("date", "<=", str(end_date)).stream())
        return [_food_row(d) for d in docs]

    def add_food_log(date_val, meal_type, food_name, food_key, quantity_g, nutrition):
        ref = _db().collection("food_logs").document()
        ref.set({
            "date": str(date_val), "meal_type": meal_type,
            "food_name": food_name, "food_key": food_key,
            "quantity_g": quantity_g, "nutrition": nutrition,
            "created_at": datetime.utcnow().isoformat(),
        })
        return ref.id

    def delete_food_log(log_id):
        _db().collection("food_logs").document(log_id).delete()

    def get_streak():
        start = str(date.today() - timedelta(days=365))
        docs = (_db().collection("food_logs")
                .where("date", ">=", start).select(["date"]).stream())
        dates_with_logs = {d.to_dict()["date"] for d in docs}
        streak, cursor = 0, date.today()
        while str(cursor) in dates_with_logs:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    # ── Water logs ─────────────────────────────────────────────────────────────

    def _water_row(doc):
        d = doc.to_dict()
        ts = d.get("created_at", datetime.utcnow().isoformat())
        return _Row(
            id=doc.id,
            date=date.fromisoformat(d["date"]),
            amount_ml=d.get("amount_ml", 0),
            created_at=datetime.fromisoformat(ts) if isinstance(ts, str) else ts,
        )

    def get_water_logs_today():
        docs = list(_db().collection("water_logs")
                    .where("date", "==", str(date.today())).stream())
        return sorted([_water_row(d) for d in docs], key=lambda x: x.created_at)

    def get_water_today():
        return sum(l.amount_ml for l in get_water_logs_today())

    def get_water_logs_range(start_date, end_date):
        docs = list(_db().collection("water_logs")
                    .where("date", ">=", str(start_date))
                    .where("date", "<=", str(end_date)).stream())
        return [_water_row(d) for d in docs]

    def add_water_log(date_val, amount_ml):
        ref = _db().collection("water_logs").document()
        ref.set({"date": str(date_val), "amount_ml": amount_ml,
                 "created_at": datetime.utcnow().isoformat()})
        return ref.id

    def delete_water_log(log_id):
        _db().collection("water_logs").document(log_id).delete()

    # ── Weight logs ────────────────────────────────────────────────────────────

    def _weight_row(doc):
        d = doc.to_dict()
        return _Row(
            id=doc.id,
            date=date.fromisoformat(d["date"]),
            weight_kg=d.get("weight_kg", 0.0),
            notes=d.get("notes", ""),
            created_at=d.get("created_at", ""),
        )

    def get_weight_for_date(target_date):
        docs = list(_db().collection("weight_logs")
                    .where("date", "==", str(target_date)).limit(1).stream())
        return _weight_row(docs[0]) if docs else None

    def get_weight_range(start_date, end_date):
        docs = list(_db().collection("weight_logs")
                    .where("date", ">=", str(start_date))
                    .where("date", "<=", str(end_date)).stream())
        return sorted([_weight_row(d) for d in docs], key=lambda x: x.date)

    def get_weight_history(limit=30):
        docs = list(_db().collection("weight_logs")
                    .order_by("date", direction="DESCENDING").limit(limit).stream())
        return list(reversed([_weight_row(d) for d in docs]))

    def upsert_weight_log(date_val, weight_kg, notes=""):
        existing = get_weight_for_date(date_val)
        if existing:
            _db().collection("weight_logs").document(existing.id).update(
                {"weight_kg": weight_kg, "notes": notes}
            )
        else:
            _db().collection("weight_logs").document().set({
                "date": str(date_val), "weight_kg": weight_kg, "notes": notes,
                "created_at": datetime.utcnow().isoformat(),
            })

    # ── Mindfulness logs ───────────────────────────────────────────────────────

    def _mind_row(doc):
        d = doc.to_dict()
        ts = d.get("created_at", datetime.utcnow().isoformat())
        return _Row(
            id=doc.id,
            date=date.fromisoformat(d["date"]),
            activity_type=d.get("activity_type", "meditation"),
            duration_minutes=d.get("duration_minutes", 0),
            notes=d.get("notes", ""),
            mood_before=d.get("mood_before", 5),
            mood_after=d.get("mood_after", 5),
            created_at=datetime.fromisoformat(ts) if isinstance(ts, str) else ts,
        )

    def get_mindfulness_today():
        docs = list(_db().collection("mindfulness_logs")
                    .where("date", "==", str(date.today())).limit(1).stream())
        return _mind_row(docs[0]) if docs else None

    def get_mindfulness_logs(limit=20):
        docs = list(_db().collection("mindfulness_logs")
                    .order_by("created_at", direction="DESCENDING").limit(limit).stream())
        return [_mind_row(d) for d in docs]

    def get_mindfulness_for_range(start_date, end_date):
        docs = list(_db().collection("mindfulness_logs")
                    .where("date", ">=", str(start_date))
                    .where("date", "<=", str(end_date)).stream())
        return [_mind_row(d) for d in docs]

    def add_mindfulness_log(date_val, activity_type, duration_minutes, notes,
                            mood_before, mood_after):
        ref = _db().collection("mindfulness_logs").document()
        ref.set({
            "date": str(date_val), "activity_type": activity_type,
            "duration_minutes": duration_minutes, "notes": notes,
            "mood_before": mood_before, "mood_after": mood_after,
            "created_at": datetime.utcnow().isoformat(),
        })
        return ref.id

    def delete_mindfulness_log(log_id):
        _db().collection("mindfulness_logs").document(log_id).delete()

    # ── Chat messages ──────────────────────────────────────────────────────────

    def _chat_row(doc):
        d = doc.to_dict()
        ts = d.get("created_at", datetime.utcnow().isoformat())
        return _Row(
            id=doc.id,
            role=d.get("role", "user"),
            content=d.get("content", ""),
            category=d.get("category", "general"),
            created_at=datetime.fromisoformat(ts) if isinstance(ts, str) else ts,
        )

    def get_chat_messages(limit=50):
        docs = list(_db().collection("chat_messages")
                    .order_by("created_at", direction="DESCENDING").limit(limit).stream())
        return list(reversed([_chat_row(d) for d in docs]))

    def add_chat_message(role, content, category="general"):
        ref = _db().collection("chat_messages").document()
        ref.set({"role": role, "content": content, "category": category,
                 "created_at": datetime.utcnow().isoformat()})
        return ref.id

    def clear_chat_messages():
        docs = list(_db().collection("chat_messages").stream())
        batch = _db().batch()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()

    # ── Saved recipes ──────────────────────────────────────────────────────────

    def _recipe_row(doc):
        d = doc.to_dict()
        ts = d.get("created_at", datetime.utcnow().isoformat())
        try:
            dt = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            dt = datetime.utcnow()
        return _Row(
            id=doc.id,
            name=d.get("name", ""),
            content=d.get("content", ""),
            source=d.get("source", "ai_coach"),
            created_at=dt,
        )

    def get_saved_recipes():
        docs = list(_db().collection("saved_recipes")
                    .order_by("created_at", direction="DESCENDING").stream())
        return [_recipe_row(d) for d in docs]

    def add_saved_recipe(name, content, source="ai_coach"):
        ref = _db().collection("saved_recipes").document()
        ref.set({"name": name, "content": content, "source": source,
                 "created_at": datetime.utcnow().isoformat()})
        return ref.id

    def delete_saved_recipe(recipe_id):
        _db().collection("saved_recipes").document(recipe_id).delete()


# ─────────────────────────────────────────────────────────────────────────────
#  SQLAlchemy / SQLite backend  (local dev + existing test suite)
# ─────────────────────────────────────────────────────────────────────────────
else:
    from database import db as _db_sa
    from models import (
        UserProfile, FoodLog, MindfulnessLog, WeightLog,
        WaterLog, ChatMessage, SavedRecipe,
    )

    def init_store(app):
        _db_sa.init_app(app)
        with app.app_context():
            _db_sa.create_all()
            from sqlalchemy import event
            from sqlalchemy.engine import Engine
            import sqlite3

            @event.listens_for(Engine, "connect")
            def _set_pragmas(dbapi_conn, _record):
                if isinstance(dbapi_conn, sqlite3.Connection):
                    cur = dbapi_conn.cursor()
                    cur.execute("PRAGMA journal_mode=WAL")
                    cur.execute("PRAGMA synchronous=NORMAL")
                    cur.execute("PRAGMA cache_size=10000")
                    cur.close()

            if not UserProfile.query.first():
                _db_sa.session.add(UserProfile())
                _db_sa.session.commit()

    # Profile
    def get_profile():
        return UserProfile.query.first()

    def save_profile(updates):
        profile = UserProfile.query.first()
        for k, v in updates.items():
            setattr(profile, k, v)
        _db_sa.session.commit()

    # Food logs
    def get_today_logs():
        return FoodLog.query.filter_by(date=date.today()).order_by(FoodLog.created_at).all()

    def get_food_logs_for_date(target_date):
        return FoodLog.query.filter_by(date=target_date).all()

    def get_food_logs_range(start_date, end_date):
        return FoodLog.query.filter(
            FoodLog.date >= start_date, FoodLog.date <= end_date
        ).all()

    def add_food_log(date_val, meal_type, food_name, food_key, quantity_g, nutrition):
        log = FoodLog(date=date_val, meal_type=meal_type, food_name=food_name,
                      food_key=food_key, quantity_g=quantity_g)
        log.nutrition = nutrition
        _db_sa.session.add(log)
        _db_sa.session.commit()
        return str(log.id)

    def delete_food_log(log_id):
        log = FoodLog.query.get_or_404(int(log_id))
        _db_sa.session.delete(log)
        _db_sa.session.commit()

    def get_streak():
        streak, cursor = 0, date.today()
        while True:
            if not FoodLog.query.filter_by(date=cursor).count():
                break
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    # Water logs
    def get_water_logs_today():
        return WaterLog.query.filter_by(date=date.today()).order_by(WaterLog.created_at).all()

    def get_water_today():
        return sum(l.amount_ml for l in get_water_logs_today())

    def get_water_logs_range(start_date, end_date):
        return WaterLog.query.filter(
            WaterLog.date >= start_date, WaterLog.date <= end_date
        ).all()

    def add_water_log(date_val, amount_ml):
        log = WaterLog(date=date_val, amount_ml=amount_ml)
        _db_sa.session.add(log)
        _db_sa.session.commit()
        return str(log.id)

    def delete_water_log(log_id):
        log = WaterLog.query.get_or_404(int(log_id))
        _db_sa.session.delete(log)
        _db_sa.session.commit()

    # Weight logs
    def get_weight_for_date(target_date):
        return WeightLog.query.filter_by(date=target_date).first()

    def get_weight_range(start_date, end_date):
        return WeightLog.query.filter(
            WeightLog.date >= start_date, WeightLog.date <= end_date
        ).order_by(WeightLog.date).all()

    def get_weight_history(limit=30):
        logs = WeightLog.query.order_by(WeightLog.date.desc()).limit(limit).all()
        return list(reversed(logs))

    def upsert_weight_log(date_val, weight_kg, notes=""):
        existing = get_weight_for_date(date_val)
        if existing:
            existing.weight_kg = weight_kg
            existing.notes = notes
        else:
            _db_sa.session.add(WeightLog(date=date_val, weight_kg=weight_kg, notes=notes))
        _db_sa.session.commit()

    # Mindfulness logs
    def get_mindfulness_today():
        return MindfulnessLog.query.filter_by(date=date.today()).first()

    def get_mindfulness_logs(limit=20):
        return MindfulnessLog.query.order_by(
            MindfulnessLog.created_at.desc()
        ).limit(limit).all()

    def get_mindfulness_for_range(start_date, end_date):
        return MindfulnessLog.query.filter(
            MindfulnessLog.date >= start_date, MindfulnessLog.date <= end_date
        ).all()

    def add_mindfulness_log(date_val, activity_type, duration_minutes, notes,
                            mood_before, mood_after):
        log = MindfulnessLog(
            date=date_val, activity_type=activity_type,
            duration_minutes=duration_minutes, notes=notes,
            mood_before=mood_before, mood_after=mood_after,
        )
        _db_sa.session.add(log)
        _db_sa.session.commit()
        return str(log.id)

    def delete_mindfulness_log(log_id):
        log = MindfulnessLog.query.get_or_404(int(log_id))
        _db_sa.session.delete(log)
        _db_sa.session.commit()

    # Chat messages
    def get_chat_messages(limit=50):
        msgs = ChatMessage.query.order_by(
            ChatMessage.created_at.desc()
        ).limit(limit).all()
        return list(reversed(msgs))

    def add_chat_message(role, content, category="general"):
        msg = ChatMessage(role=role, content=content, category=category)
        _db_sa.session.add(msg)
        _db_sa.session.commit()
        return str(msg.id)

    def clear_chat_messages():
        ChatMessage.query.delete()
        _db_sa.session.commit()

    # Saved recipes
    def get_saved_recipes():
        return SavedRecipe.query.order_by(SavedRecipe.created_at.desc()).all()

    def add_saved_recipe(name, content, source="ai_coach"):
        recipe = SavedRecipe(name=name, content=content, source=source)
        _db_sa.session.add(recipe)
        _db_sa.session.commit()
        return str(recipe.id)

    def delete_saved_recipe(recipe_id):
        recipe = SavedRecipe.query.get_or_404(int(recipe_id))
        _db_sa.session.delete(recipe)
        _db_sa.session.commit()

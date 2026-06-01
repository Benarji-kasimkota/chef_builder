import os
import json
import httpx
from datetime import date, timedelta, datetime
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from database import db
from models import UserProfile, FoodLog, MindfulnessLog, WeightLog, ChatMessage
from nutrition_data import (
    FOOD_DATABASE, RDA, VITAMIN_NAMES, VITAMIN_UNITS, MINERAL_NAMES,
    AMINO_ACID_NAMES, AMINO_ACID_ROLES, search_food_local,
    calculate_nutrition_totals, calculate_deficiencies, calculate_personal_rda
)
import ai_service

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chefbuilder-dev-secret-2024")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///chefbuilder.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    if not UserProfile.query.first():
        db.session.add(UserProfile())
        db.session.commit()


def get_profile():
    return UserProfile.query.first()


def get_today_logs():
    return FoodLog.query.filter_by(date=date.today()).order_by(FoodLog.created_at).all()


def logs_to_nutrition_list(logs):
    result = []
    for log in logs:
        result.append({
            "quantity": log.quantity_g,
            "nutrition": log.nutrition
        })
    return result


def get_nutrition_for_date(target_date):
    logs = FoodLog.query.filter_by(date=target_date).all()
    if not logs:
        return None
    return calculate_nutrition_totals(logs_to_nutrition_list(logs))


# ──────────────────────────────────────────────
#  PAGES
# ──────────────────────────────────────────────

@app.route("/")
def dashboard():
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = calculate_personal_rda(
        profile.weight_kg, profile.height_cm, profile.age,
        profile.gender, profile.activity_level, profile.goal
    ) if profile else RDA
    deficiencies = calculate_deficiencies(totals, rda)
    cal_pct = min(totals["calories"] / rda["calories"] * 100, 100) if rda["calories"] else 0
    protein_pct = min(totals["protein"] / rda["protein"] * 100, 100) if rda["protein"] else 0
    mind_today = MindfulnessLog.query.filter_by(date=date.today()).first()
    mind_pct = min((mind_today.duration_minutes / 30) * 100, 100) if mind_today else 0
    return render_template("dashboard.html",
        profile=profile, totals=totals, rda=rda, deficiencies=deficiencies,
        logs=logs, cal_pct=round(cal_pct, 1), protein_pct=round(protein_pct, 1),
        mind_pct=round(mind_pct, 1), vitamin_names=VITAMIN_NAMES,
        mineral_names=MINERAL_NAMES, amino_names=AMINO_ACID_NAMES,
        today=date.today().strftime("%A, %B %d %Y")
    )


@app.route("/log")
def food_log():
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = calculate_personal_rda(
        profile.weight_kg, profile.height_cm, profile.age,
        profile.gender, profile.activity_level, profile.goal
    ) if profile else RDA
    deficiencies = calculate_deficiencies(totals, rda)
    return render_template("food_log.html",
        profile=profile, logs=logs, totals=totals, rda=rda,
        deficiencies=deficiencies, vitamin_names=VITAMIN_NAMES,
        vitamin_units=VITAMIN_UNITS, mineral_names=MINERAL_NAMES,
        amino_names=AMINO_ACID_NAMES, amino_roles=AMINO_ACID_ROLES,
        today=date.today().strftime("%A, %B %d")
    )


@app.route("/chat")
def chat_page():
    profile = get_profile()
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(50).all()
    messages = list(reversed(messages))
    return render_template("chat.html", profile=profile, messages=messages)


@app.route("/recipes")
def recipes_page():
    profile = get_profile()
    return render_template("recipes.html", profile=profile)


@app.route("/mindfulness")
def mindfulness_page():
    profile = get_profile()
    logs = MindfulnessLog.query.order_by(MindfulnessLog.created_at.desc()).limit(20).all()
    today_log = MindfulnessLog.query.filter_by(date=date.today()).first()
    return render_template("mindfulness.html", profile=profile, logs=logs, today_log=today_log)


@app.route("/profile")
def profile_page():
    profile = get_profile()
    return render_template("profile.html", profile=profile)


# ──────────────────────────────────────────────
#  API — FOOD & NUTRITION
# ──────────────────────────────────────────────

@app.route("/api/food/search")
def search_food():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])

    results = []
    local = search_food_local(query)
    for food in local:
        results.append({
            "source": "local",
            "key": food["key"],
            "name": food["name"],
            "serving_size": food["serving_size"],
            "serving_unit": food["serving_unit"],
            "calories": food["calories"],
            "protein": food["protein"],
            "carbs": food["carbs"],
            "fat": food["fat"]
        })

    if len(results) < 5:
        try:
            usda_key = os.environ.get("USDA_API_KEY", "DEMO_KEY")
            resp = httpx.get(
                "https://api.nal.usda.gov/fdc/v1/foods/search",
                params={"query": query, "api_key": usda_key,
                        "dataType": "Foundation,SR Legacy", "pageSize": 8},
                timeout=5
            )
            if resp.status_code == 200:
                for item in resp.json().get("foods", [])[:6]:
                    nutrients = {n["nutrientId"]: n["value"] for n in item.get("foodNutrients", [])}
                    results.append({
                        "source": "usda",
                        "key": f"usda_{item['fdcId']}",
                        "name": item.get("description", "Unknown"),
                        "fdcId": item["fdcId"],
                        "serving_size": 100,
                        "serving_unit": "g",
                        "calories": round(nutrients.get(1008, 0), 1),
                        "protein": round(nutrients.get(1003, 0), 1),
                        "carbs": round(nutrients.get(1005, 0), 1),
                        "fat": round(nutrients.get(1004, 0), 1)
                    })
        except Exception:
            pass

    return jsonify(results[:10])


@app.route("/api/food/detail")
def food_detail():
    key = request.args.get("key", "")
    if key.startswith("usda_"):
        fdc_id = key.replace("usda_", "")
        try:
            usda_key = os.environ.get("USDA_API_KEY", "DEMO_KEY")
            resp = httpx.get(
                f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}",
                params={"api_key": usda_key}, timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                nutrients = {n["nutrient"]["id"]: n["amount"]
                             for n in data.get("foodNutrients", []) if "amount" in n}
                nutrition = {
                    "calories": nutrients.get(1008, 0),
                    "protein": nutrients.get(1003, 0),
                    "carbs": nutrients.get(1005, 0),
                    "sugar": nutrients.get(2000, 0),
                    "fiber": nutrients.get(1079, 0),
                    "fat": nutrients.get(1004, 0),
                    "saturated_fat": nutrients.get(1258, 0),
                    "monounsaturated_fat": nutrients.get(1292, 0),
                    "polyunsaturated_fat": nutrients.get(1293, 0),
                    "omega3": nutrients.get(1404, 0),
                    "omega6": nutrients.get(1316, nutrients.get(1269, 0)),
                    "vitamins": {
                        "a": nutrients.get(1106, 0), "b1": nutrients.get(1165, 0),
                        "b2": nutrients.get(1166, 0), "b3": nutrients.get(1167, 0),
                        "b5": nutrients.get(1170, 0), "b6": nutrients.get(1175, 0),
                        "b9": nutrients.get(1177, 0), "b12": nutrients.get(1178, 0),
                        "c": nutrients.get(1162, 0), "d": nutrients.get(1114, 0),
                        "e": nutrients.get(1109, 0), "k": nutrients.get(1185, 0)
                    },
                    "minerals": {
                        "calcium": nutrients.get(1087, 0), "iron": nutrients.get(1089, 0),
                        "magnesium": nutrients.get(1090, 0), "phosphorus": nutrients.get(1091, 0),
                        "potassium": nutrients.get(1092, 0), "sodium": nutrients.get(1093, 0),
                        "zinc": nutrients.get(1095, 0), "selenium": nutrients.get(1103, 0)
                    },
                    "amino_acids": {
                        "tryptophan": nutrients.get(1210, 0),
                        "threonine": nutrients.get(1211, 0),
                        "isoleucine": nutrients.get(1212, 0),
                        "leucine": nutrients.get(1213, 0),
                        "lysine": nutrients.get(1214, 0),
                        "methionine": nutrients.get(1215, 0),
                        "phenylalanine": nutrients.get(1217, 0),
                        "valine": nutrients.get(1219, 0),
                        "histidine": nutrients.get(1221, 0)
                    }
                }
                return jsonify({"name": data.get("description", ""), "nutrition": nutrition,
                                "serving_size": 100, "serving_unit": "g"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif key in FOOD_DATABASE:
        food = FOOD_DATABASE[key]
        return jsonify({
            "name": food["name"],
            "serving_size": food["serving_size"],
            "serving_unit": food["serving_unit"],
            "nutrition": {
                "calories": food["calories"], "protein": food["protein"],
                "carbs": food["carbs"], "sugar": food.get("sugar", 0),
                "fiber": food.get("fiber", 0), "fat": food["fat"],
                "saturated_fat": food.get("saturated_fat", 0),
                "monounsaturated_fat": food.get("monounsaturated_fat", 0),
                "polyunsaturated_fat": food.get("polyunsaturated_fat", 0),
                "omega3": food.get("omega3", 0), "omega6": food.get("omega6", 0),
                "vitamins": food.get("vitamins", {}),
                "minerals": food.get("minerals", {}),
                "amino_acids": food.get("amino_acids", {})
            }
        })
    return jsonify({"error": "Food not found"}), 404


@app.route("/api/food/log", methods=["POST"])
def log_food():
    data = request.json
    log = FoodLog(
        date=date.fromisoformat(data.get("date", str(date.today()))),
        meal_type=data.get("meal_type", "lunch"),
        food_name=data["food_name"],
        food_key=data.get("food_key", ""),
        quantity_g=float(data.get("quantity_g", 100))
    )
    log.nutrition = data.get("nutrition", {})
    db.session.add(log)
    db.session.commit()
    return jsonify({"success": True, "id": log.id})


@app.route("/api/food/log/<int:log_id>", methods=["DELETE"])
def delete_food_log(log_id):
    log = FoodLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/nutrition/today")
def nutrition_today():
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = calculate_personal_rda(
        profile.weight_kg, profile.height_cm, profile.age,
        profile.gender, profile.activity_level, profile.goal
    ) if profile else RDA
    deficiencies = calculate_deficiencies(totals, rda)
    return jsonify({"totals": totals, "rda": rda, "deficiencies": deficiencies})


@app.route("/api/calendar")
def calendar_data():
    today = date.today()
    start = today.replace(day=1)
    year, month = today.year, today.month
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)

    profile = get_profile()
    rda = calculate_personal_rda(
        profile.weight_kg, profile.height_cm, profile.age,
        profile.gender, profile.activity_level, profile.goal
    ) if profile else RDA

    logs_by_date = defaultdict(list)
    all_logs = FoodLog.query.filter(FoodLog.date >= start, FoodLog.date <= end).all()
    for log in all_logs:
        logs_by_date[str(log.date)].append({
            "quantity": log.quantity_g, "nutrition": log.nutrition
        })

    mind_by_date = {}
    mind_logs = MindfulnessLog.query.filter(
        MindfulnessLog.date >= start, MindfulnessLog.date <= end).all()
    for ml in mind_logs:
        mind_by_date[str(ml.date)] = ml.duration_minutes

    result = {}
    cursor = start
    while cursor <= end:
        d = str(cursor)
        food_data = logs_by_date.get(d, [])
        totals = calculate_nutrition_totals(food_data) if food_data else {}
        cal_pct = min(totals.get("calories", 0) / rda["calories"] * 100, 100) if food_data else 0
        protein_pct = min(totals.get("protein", 0) / rda["protein"] * 100, 100) if food_data else 0
        mind_mins = mind_by_date.get(d, 0)
        mind_pct = min(mind_mins / 30 * 100, 100)
        result[d] = {
            "cal_pct": round(cal_pct, 1),
            "protein_pct": round(protein_pct, 1),
            "mind_pct": round(mind_pct, 1),
            "has_data": bool(food_data),
            "calories": round(totals.get("calories", 0))
        }
        cursor += timedelta(days=1)
    return jsonify(result)


# ──────────────────────────────────────────────
#  API — AI FEATURES
# ──────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.json
    user_message = data.get("message", "").strip()
    category = data.get("category", "general")
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    db.session.add(ChatMessage(role="user", content=user_message, category=category))
    db.session.commit()
    history = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(20).all()
    history = list(reversed(history))
    messages = [{"role": m.role, "content": m.content} for m in history]

    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = calculate_personal_rda(
        profile.weight_kg, profile.height_cm, profile.age,
        profile.gender, profile.activity_level, profile.goal
    ) if profile else RDA
    deficiencies = calculate_deficiencies(totals, rda)

    try:
        reply = ai_service.chat(
            messages=messages,
            today_nutrition=totals,
            deficiencies=deficiencies,
            profile={"name": profile.name, "goal": profile.goal,
                     "dietary_preference": profile.dietary_preference} if profile else {}
        )
    except Exception as e:
        reply = f"I'm having trouble connecting right now. Please check your API key. Error: {str(e)}"

    msg = ChatMessage(role="assistant", content=reply, category=category)
    db.session.add(msg)
    db.session.commit()
    return jsonify({"reply": reply, "id": msg.id})


@app.route("/api/recipes/suggest", methods=["POST"])
def suggest_recipes():
    data = request.json or {}
    preferences = data.get("preferences", "")
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = calculate_personal_rda(
        profile.weight_kg, profile.height_cm, profile.age,
        profile.gender, profile.activity_level, profile.goal
    ) if profile else RDA
    deficiencies = calculate_deficiencies(totals, rda)
    try:
        raw = ai_service.generate_recipe_suggestions(
            profile={"name": profile.name if profile else "User",
                     "goal": profile.goal if profile else "maintain",
                     "dietary_preference": profile.dietary_preference if profile else "omnivore"},
            today_nutrition=totals,
            deficiencies=deficiencies,
            preferences=preferences
        )
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return jsonify(json.loads(match.group()))
        return jsonify({"recipes": [], "raw": raw})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/insight")
def daily_insight():
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = calculate_personal_rda(
        profile.weight_kg, profile.height_cm, profile.age,
        profile.gender, profile.activity_level, profile.goal
    ) if profile else RDA
    deficiencies = calculate_deficiencies(totals, rda)
    try:
        insight = ai_service.get_daily_insight(
            today_nutrition=totals,
            deficiencies=deficiencies,
            profile={"goal": profile.goal if profile else "maintain"}
        )
        return jsonify({"insight": insight})
    except Exception as e:
        return jsonify({"insight": "Log your meals today to get personalized AI insights!"})


@app.route("/api/meal/analyze", methods=["POST"])
def analyze_meal():
    data = request.json or {}
    try:
        result = ai_service.analyze_meal_and_suggest(
            data.get("food_name", ""), data.get("ingredients", ""))
        return jsonify({"analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
#  API — MINDFULNESS
# ──────────────────────────────────────────────

@app.route("/api/mindfulness/log", methods=["POST"])
def log_mindfulness():
    data = request.json
    log = MindfulnessLog(
        date=date.fromisoformat(data.get("date", str(date.today()))),
        activity_type=data.get("activity_type", "meditation"),
        duration_minutes=int(data.get("duration_minutes", 0)),
        notes=data.get("notes", ""),
        mood_before=int(data.get("mood_before", 5)),
        mood_after=int(data.get("mood_after", 5))
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"success": True, "id": log.id})


@app.route("/api/mindfulness/log/<int:log_id>", methods=["DELETE"])
def delete_mindfulness_log(log_id):
    log = MindfulnessLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    return jsonify({"success": True})


# ──────────────────────────────────────────────
#  API — PROFILE
# ──────────────────────────────────────────────

@app.route("/api/profile", methods=["GET", "POST"])
def profile_api():
    profile = get_profile()
    if request.method == "GET":
        return jsonify({
            "name": profile.name, "age": profile.age, "gender": profile.gender,
            "weight_kg": profile.weight_kg, "height_cm": profile.height_cm,
            "activity_level": profile.activity_level, "goal": profile.goal,
            "dietary_preference": profile.dietary_preference, "allergies": profile.allergies
        })
    data = request.json
    for field in ["name", "gender", "activity_level", "goal", "dietary_preference", "allergies"]:
        if field in data:
            setattr(profile, field, data[field])
    for field in ["age"]:
        if field in data:
            setattr(profile, field, int(data[field]))
    for field in ["weight_kg", "height_cm"]:
        if field in data:
            setattr(profile, field, float(data[field]))
    db.session.commit()
    return jsonify({"success": True})


# ──────────────────────────────────────────────
#  TEMPLATE FILTERS & CONTEXT
# ──────────────────────────────────────────────

@app.template_filter("pct_color")
def pct_color(pct):
    if pct >= 80:
        return "green"
    elif pct >= 40:
        return "amber"
    return "red"


@app.template_filter("fmt_num")
def fmt_num(val):
    if val is None:
        return "0"
    if isinstance(val, float):
        return f"{val:.1f}" if val < 100 else f"{val:.0f}"
    return str(val)


@app.context_processor
def inject_now():
    return {"now": datetime.now()}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

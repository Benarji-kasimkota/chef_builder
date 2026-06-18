import os
import io
import re
import csv
import json
import base64
import httpx
from datetime import date, timedelta, datetime
from collections import defaultdict
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
from store import (
    init_store,
    get_profile, save_profile,
    get_today_logs, get_food_logs_range,
    add_food_log, delete_food_log, get_streak,
    get_water_today, get_water_logs_today, get_water_logs_range,
    add_water_log, delete_water_log,
    get_weight_range, get_weight_history, upsert_weight_log,
    get_mindfulness_today, get_mindfulness_logs, get_mindfulness_for_range,
    add_mindfulness_log, delete_mindfulness_log,
    get_chat_messages, add_chat_message, clear_chat_messages,
    get_saved_recipes, add_saved_recipe, delete_saved_recipe,
)
from nutrition_data import (
    FOOD_DATABASE, RDA, VITAMIN_NAMES, VITAMIN_UNITS, MINERAL_NAMES,
    AMINO_ACID_NAMES, AMINO_ACID_ROLES, search_food_local,
    calculate_nutrition_totals, calculate_deficiencies, calculate_personal_rda
)
import ai_service

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chefbuilder-dev-secret-2024")

# SQLAlchemy URI still read by store.py's SQLite backend when FIREBASE_CREDENTIALS is unset
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///chefbuilder.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 10, "max_overflow": 20, "pool_timeout": 30,
    "connect_args": {"check_same_thread": False, "timeout": 20},
}

os.makedirs(app.instance_path, exist_ok=True)
init_store(app)


# ─────────────────────────────────────────────────────────────────────────────
#  Shared helpers (work with Row objects from both backends)
# ─────────────────────────────────────────────────────────────────────────────

def logs_to_nutrition_list(logs):
    # nutrition is pre-scaled to quantity_g when logged; pass quantity=100 so ratio=1
    return [{"quantity": 100, "nutrition": log.nutrition} for log in logs]


def get_effective_rda(profile):
    rda = calculate_personal_rda(
        profile.weight_kg, profile.height_cm, profile.age,
        profile.gender, profile.activity_level, profile.goal
    ) if profile else dict(RDA)
    if profile:
        if profile.custom_calories:
            rda["calories"] = profile.custom_calories
        if profile.custom_protein:
            rda["protein"] = profile.custom_protein
        if profile.custom_carbs:
            rda["carbs"] = profile.custom_carbs
        if profile.custom_fat:
            rda["fat"] = profile.custom_fat
    return rda


# ─────────────────────────────────────────────────────────────────────────────
#  PAGES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    profile = get_profile()
    if profile and not profile.onboarding_complete:
        return render_template("onboarding.html", profile=profile)
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = get_effective_rda(profile)
    deficiencies = calculate_deficiencies(totals, rda)
    cal_pct = min(totals["calories"] / rda["calories"] * 100, 100) if rda["calories"] else 0
    protein_pct = min(totals["protein"] / rda["protein"] * 100, 100) if rda["protein"] else 0
    mind_today = get_mindfulness_today()
    mind_pct = min((mind_today.duration_minutes / 30) * 100, 100) if mind_today else 0
    water_ml = get_water_today()
    water_goal = profile.water_goal_ml if profile else 2500
    water_pct = min(water_ml / water_goal * 100, 100) if water_goal else 0
    streak = get_streak()
    return render_template("dashboard.html",
        profile=profile, totals=totals, rda=rda, deficiencies=deficiencies,
        logs=logs, cal_pct=round(cal_pct, 1), protein_pct=round(protein_pct, 1),
        mind_pct=round(mind_pct, 1), vitamin_names=VITAMIN_NAMES,
        mineral_names=MINERAL_NAMES, amino_names=AMINO_ACID_NAMES,
        today=date.today().strftime("%A, %B %d %Y"),
        water_ml=water_ml, water_goal=water_goal, water_pct=round(water_pct, 1),
        streak=streak
    )


@app.route("/log")
def food_log():
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = get_effective_rda(profile)
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
    clear_chat_messages()
    return render_template("chat.html", profile=profile, messages=[])


@app.route("/recipes")
def recipes_page():
    profile = get_profile()
    return render_template("recipes.html", profile=profile)


@app.route("/mindfulness")
def mindfulness_page():
    profile = get_profile()
    logs = get_mindfulness_logs(limit=20)
    today_log = get_mindfulness_today()
    return render_template("mindfulness.html", profile=profile, logs=logs, today_log=today_log)


@app.route("/profile")
def profile_page():
    profile = get_profile()
    return render_template("profile.html", profile=profile)


@app.route("/progress")
def progress_page():
    profile = get_profile()
    return render_template("progress.html", profile=profile)


@app.route("/planner")
def planner_page():
    profile = get_profile()
    return render_template("planner.html", profile=profile)


@app.route("/grocery")
def grocery_page():
    profile = get_profile()
    return render_template("grocery.html", profile=profile)


@app.route("/onboarding")
def onboarding_page():
    profile = get_profile()
    return render_template("onboarding.html", profile=profile)


# ─────────────────────────────────────────────────────────────────────────────
#  API — FOOD & NUTRITION
# ─────────────────────────────────────────────────────────────────────────────

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


@app.route("/api/food/barcode/<barcode>")
def food_barcode(barcode):
    """Look up food by barcode using Open Food Facts (free, no key needed)."""
    try:
        resp = httpx.get(
            f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json",
            timeout=6,
            headers={"User-Agent": "ChefBuilder/1.0"}
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == 1:
                p = data["product"]
                n = p.get("nutriments", {})
                name = p.get("product_name") or p.get("generic_name") or "Unknown product"
                return jsonify({
                    "found": True,
                    "name": name,
                    "brand": p.get("brands", ""),
                    "serving_size": 100,
                    "serving_unit": "g",
                    "nutrition": {
                        "calories": n.get("energy-kcal_100g", n.get("energy_100g", 0) / 4.184),
                        "protein": n.get("proteins_100g", 0),
                        "carbs": n.get("carbohydrates_100g", 0),
                        "sugar": n.get("sugars_100g", 0),
                        "fiber": n.get("fiber_100g", 0),
                        "fat": n.get("fat_100g", 0),
                        "saturated_fat": n.get("saturated-fat_100g", 0),
                        "sodium": n.get("sodium_100g", 0) * 1000,
                        "vitamins": {}, "minerals": {}, "amino_acids": {}
                    }
                })
    except Exception as e:
        return jsonify({"found": False, "error": str(e)}), 500
    return jsonify({"found": False})


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
    log_id = add_food_log(
        date_val=date.fromisoformat(data.get("date", str(date.today()))),
        meal_type=data.get("meal_type", "lunch"),
        food_name=data["food_name"],
        food_key=data.get("food_key", ""),
        quantity_g=float(data.get("quantity_g", 100)),
        nutrition=data.get("nutrition", {}),
    )
    return jsonify({"success": True, "id": log_id})


@app.route("/api/food/log/<log_id>", methods=["DELETE"])
def delete_food_log_route(log_id):
    delete_food_log(log_id)
    return jsonify({"success": True})


@app.route("/api/nutrition/today")
def nutrition_today():
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = get_effective_rda(profile)
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
    rda = get_effective_rda(profile)

    logs_by_date = defaultdict(list)
    for log in get_food_logs_range(start, end):
        logs_by_date[str(log.date)].append({"quantity": 100, "nutrition": log.nutrition})

    mind_by_date = {}
    for ml in get_mindfulness_for_range(start, end):
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


@app.route("/api/progress/history")
def progress_history():
    """Return 30-day history for charts."""
    days = int(request.args.get("days", 30))
    today = date.today()
    start = today - timedelta(days=days - 1)

    profile = get_profile()
    rda = get_effective_rda(profile)

    logs_by_date = defaultdict(list)
    for log in get_food_logs_range(start, today):
        logs_by_date[str(log.date)].append({"quantity": 100, "nutrition": log.nutrition})

    water_by_date = defaultdict(int)
    for wl in get_water_logs_range(start, today):
        water_by_date[str(wl.date)] += wl.amount_ml

    weight_by_date = {str(wl.date): wl.weight_kg for wl in get_weight_range(start, today)}

    result = []
    cursor = start
    while cursor <= today:
        d = str(cursor)
        food_data = logs_by_date.get(d, [])
        totals = calculate_nutrition_totals(food_data) if food_data else {}
        result.append({
            "date": d,
            "calories": round(totals.get("calories", 0)),
            "protein": round(totals.get("protein", 0), 1),
            "carbs": round(totals.get("carbs", 0), 1),
            "fat": round(totals.get("fat", 0), 1),
            "fiber": round(totals.get("fiber", 0), 1),
            "water_ml": water_by_date.get(d, 0),
            "weight_kg": weight_by_date.get(d),
            "has_data": bool(food_data)
        })
        cursor += timedelta(days=1)

    return jsonify({"history": result, "rda": rda})


@app.route("/api/streak")
def streak_api():
    return jsonify({"streak": get_streak()})


# ─────────────────────────────────────────────────────────────────────────────
#  API — WATER
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/water/today")
def water_today():
    profile = get_profile()
    total = get_water_today()
    goal = profile.water_goal_ml if profile else 2500
    logs = get_water_logs_today()
    return jsonify({
        "total_ml": total,
        "goal_ml": goal,
        "pct": round(min(total / goal * 100, 100), 1) if goal else 0,
        "logs": [{"id": l.id, "amount_ml": l.amount_ml,
                  "created_at": l.created_at.strftime("%H:%M")} for l in logs]
    })


@app.route("/api/water/log", methods=["POST"])
def log_water():
    data = request.json
    amount = int(data.get("amount_ml", 250))
    log_id = add_water_log(date.today(), amount)
    total = get_water_today()
    profile = get_profile()
    goal = profile.water_goal_ml if profile else 2500
    return jsonify({"success": True, "id": log_id, "total_ml": total,
                    "pct": round(min(total / goal * 100, 100), 1)})


@app.route("/api/water/log/<log_id>", methods=["DELETE"])
def delete_water_log_route(log_id):
    delete_water_log(log_id)
    return jsonify({"success": True})


# ─────────────────────────────────────────────────────────────────────────────
#  API — WEIGHT
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/weight/log", methods=["POST"])
def log_weight():
    data = request.json
    weight_kg = float(data["weight_kg"])
    upsert_weight_log(
        date.fromisoformat(data.get("date", str(date.today()))),
        weight_kg,
        data.get("notes", "")
    )
    save_profile({"weight_kg": weight_kg})
    return jsonify({"success": True})


@app.route("/api/weight/history")
def weight_history():
    logs = get_weight_history(limit=30)
    return jsonify([{"date": str(l.date), "weight_kg": l.weight_kg} for l in logs])


# ─────────────────────────────────────────────────────────────────────────────
#  API — AI FEATURES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.json
    user_message = data.get("message", "").strip()
    category = data.get("category", "general")
    language = data.get("language", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    add_chat_message("user", user_message, category)
    history = get_chat_messages(limit=20)
    messages = [{"role": m.role, "content": m.content} for m in history]

    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = get_effective_rda(profile)
    deficiencies = calculate_deficiencies(totals, rda)
    if language:
        messages[-1]["content"] = f"[Respond in {language}] {messages[-1]['content']}"

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

    msg_id = add_chat_message("assistant", reply, category)
    return jsonify({"reply": reply, "id": msg_id})


@app.route("/api/recipes/suggest", methods=["POST"])
def suggest_recipes():
    data = request.json or {}
    preferences = data.get("preferences", "")
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = get_effective_rda(profile)
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
    rda = get_effective_rda(profile)
    deficiencies = calculate_deficiencies(totals, rda)
    try:
        insight = ai_service.get_daily_insight(
            today_nutrition=totals,
            deficiencies=deficiencies,
            profile={"goal": profile.goal if profile else "maintain"}
        )
        return jsonify({"insight": insight})
    except Exception:
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


@app.route("/api/meal/image", methods=["POST"])
def analyze_meal_image():
    """Analyze a meal photo using Gemini Vision."""
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400
    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    mime = file.mimetype or "image/jpeg"
    if mime not in allowed:
        return jsonify({"error": "Unsupported image type"}), 400

    image_data = base64.standard_b64encode(file.read()).decode("utf-8")
    profile = get_profile()
    try:
        result = ai_service.analyze_meal_image(
            image_data=image_data,
            mime_type=mime,
            profile={"goal": profile.goal if profile else "maintain",
                     "dietary_preference": profile.dietary_preference if profile else "omnivore"}
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/weekly-report")
def weekly_report():
    today = date.today()
    start = today - timedelta(days=6)

    profile = get_profile()

    food_by_date = defaultdict(list)
    for log in get_food_logs_range(start, today):
        food_by_date[str(log.date)].append({"quantity": 100, "nutrition": log.nutrition})

    water_by_date = defaultdict(int)
    for wl in get_water_logs_range(start, today):
        water_by_date[str(wl.date)] += wl.amount_ml

    week_data = []
    cursor = start
    while cursor <= today:
        d = str(cursor)
        food_data = food_by_date.get(d, [])
        totals = calculate_nutrition_totals(food_data) if food_data else {}
        week_data.append({
            "date": cursor.strftime("%A %b %d"),
            "calories": totals.get("calories", 0),
            "protein": totals.get("protein", 0),
            "water_ml": water_by_date.get(d, 0)
        })
        cursor += timedelta(days=1)

    try:
        report = ai_service.generate_weekly_report(
            week_data=week_data,
            profile={"name": profile.name if profile else "User",
                     "goal": profile.goal if profile else "maintain",
                     "dietary_preference": profile.dietary_preference if profile else "omnivore"}
        )
        return jsonify({"report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/grocery/generate", methods=["POST"])
def generate_grocery():
    data = request.json or {}
    preferences = data.get("preferences", "")
    profile = get_profile()

    today = date.today()
    start = today - timedelta(days=6)
    all_deficiencies = {"vitamins": {}, "minerals": {}}

    food_by_date = defaultdict(list)
    for log in get_food_logs_range(start, today):
        food_by_date[str(log.date)].append({"quantity": 100, "nutrition": log.nutrition})

    rda = get_effective_rda(profile)
    for food_data in food_by_date.values():
        totals = calculate_nutrition_totals(food_data)
        defics = calculate_deficiencies(totals, rda)
        for k, v in defics.get("vitamins", {}).items():
            all_deficiencies["vitamins"][k] = all_deficiencies["vitamins"].get(k, 0) + v
        for k, v in defics.get("minerals", {}).items():
            all_deficiencies["minerals"][k] = all_deficiencies["minerals"].get(k, 0) + v

    try:
        result = ai_service.generate_grocery_list(
            profile={"goal": profile.goal if profile else "maintain",
                     "dietary_preference": profile.dietary_preference if profile else "omnivore",
                     "allergies": profile.allergies if profile else ""},
            week_deficiencies=all_deficiencies,
            preferences=preferences
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/meal-plan/generate", methods=["POST"])
def generate_meal_plan():
    data = request.json or {}
    days = int(data.get("days", 7))
    preferences = data.get("preferences", "")
    profile = get_profile()
    logs = get_today_logs()
    totals = calculate_nutrition_totals(logs_to_nutrition_list(logs))
    rda = get_effective_rda(profile)
    deficiencies = calculate_deficiencies(totals, rda)
    try:
        result = ai_service.generate_meal_plan(
            profile={"goal": profile.goal if profile else "maintain",
                     "dietary_preference": profile.dietary_preference if profile else "omnivore",
                     "allergies": profile.allergies if profile else ""},
            today_nutrition=totals,
            deficiencies=deficiencies,
            days=days,
            preferences=preferences
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dish/calculate", methods=["POST"])
def calculate_dish():
    data = request.json or {}
    dish_name = data.get("dish_name", "Custom Dish").strip()
    ingredients = data.get("ingredients", [])
    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400
    try:
        result = ai_service.calculate_dish_nutrition(
            dish_name=dish_name,
            ingredients=ingredients,
            cooking_method=data.get("cooking_method", ""),
            servings=int(data.get("servings", 1))
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/translate", methods=["POST"])
def translate_ingredient():
    data = request.json or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        result = ai_service.translate_ingredient(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "english_name": text}), 500


@app.route("/api/recipes/from-ingredients", methods=["POST"])
def recipes_from_ingredients():
    data = request.json or {}
    ingredients = data.get("ingredients", [])
    if isinstance(ingredients, str):
        ingredients = [i.strip() for i in ingredients.split(",") if i.strip()]
    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400
    try:
        result = ai_service.generate_from_ingredients(
            ingredients=ingredients,
            dietary_prefs=data.get("dietary_prefs", ""),
            cuisine_hint=data.get("cuisine_hint", "")
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/recipes/variations", methods=["POST"])
def recipe_variations():
    data = request.json or {}
    recipe_name = data.get("recipe_name", "").strip()
    if not recipe_name:
        return jsonify({"error": "No recipe name provided"}), 400
    try:
        result = ai_service.generate_recipe_variations(
            recipe_name=recipe_name,
            base_ingredients=data.get("base_ingredients", ""),
            dietary_prefs=data.get("dietary_prefs", "")
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/recipes/ayurvedic-check", methods=["POST"])
def ayurvedic_check():
    data = request.json or {}
    ingredients = data.get("ingredients", [])
    if isinstance(ingredients, str):
        ingredients = [i.strip() for i in ingredients.split(",") if i.strip()]
    if not ingredients:
        return jsonify({"error": "No ingredients provided"}), 400
    try:
        result = ai_service.check_ayurvedic_compatibility(
            ingredients=ingredients,
            dosha=data.get("dosha", "")
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/recipes/dosha", methods=["POST"])
def dosha_recipes():
    data = request.json or {}
    dosha = data.get("dosha", "").strip()
    if dosha not in ("vata", "pitta", "kapha", "tridoshic"):
        return jsonify({"error": "Invalid dosha. Use: vata, pitta, kapha, tridoshic"}), 400
    try:
        result = ai_service.get_dosha_recipes(
            dosha=dosha,
            dietary_pref=data.get("dietary_pref", ""),
            season=data.get("season", "")
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  API — MINDFULNESS
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/mindfulness/log", methods=["POST"])
def log_mindfulness():
    data = request.json
    log_id = add_mindfulness_log(
        date_val=date.fromisoformat(data.get("date", str(date.today()))),
        activity_type=data.get("activity_type", "meditation"),
        duration_minutes=int(data.get("duration_minutes", 0)),
        notes=data.get("notes", ""),
        mood_before=int(data.get("mood_before", 5)),
        mood_after=int(data.get("mood_after", 5)),
    )
    return jsonify({"success": True, "id": log_id})


@app.route("/api/mindfulness/log/<log_id>", methods=["DELETE"])
def delete_mindfulness_log_route(log_id):
    delete_mindfulness_log(log_id)
    return jsonify({"success": True})


# ─────────────────────────────────────────────────────────────────────────────
#  API — PROFILE
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/profile", methods=["GET", "POST"])
def profile_api():
    profile = get_profile()
    if request.method == "GET":
        return jsonify({
            "name": profile.name, "age": profile.age, "gender": profile.gender,
            "weight_kg": profile.weight_kg, "height_cm": profile.height_cm,
            "activity_level": profile.activity_level, "goal": profile.goal,
            "dietary_preference": profile.dietary_preference, "allergies": profile.allergies,
            "custom_calories": profile.custom_calories, "custom_protein": profile.custom_protein,
            "custom_carbs": profile.custom_carbs, "custom_fat": profile.custom_fat,
            "water_goal_ml": profile.water_goal_ml
        })
    data = request.json
    updates = {}
    for field in ["name", "gender", "activity_level", "goal", "dietary_preference", "allergies"]:
        if field in data:
            updates[field] = data[field]
    for field in ["age", "custom_calories", "custom_protein", "custom_carbs",
                  "custom_fat", "water_goal_ml"]:
        if field in data:
            updates[field] = int(data[field])
    for field in ["weight_kg", "height_cm"]:
        if field in data:
            updates[field] = float(data[field])
    if "onboarding_complete" in data:
        updates["onboarding_complete"] = bool(data["onboarding_complete"])
    save_profile(updates)
    return jsonify({"success": True})


# ─────────────────────────────────────────────────────────────────────────────
#  API — EXPORT
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/export/csv")
def export_csv():
    days = int(request.args.get("days", 30))
    today = date.today()
    start = today - timedelta(days=days - 1)
    logs = sorted(get_food_logs_range(start, today), key=lambda l: (l.date, l.created_at))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Meal Type", "Food", "Quantity (g)",
                     "Calories", "Protein (g)", "Carbs (g)", "Fat (g)",
                     "Fiber (g)", "Sugar (g)"])
    for log in logs:
        n = log.nutrition
        writer.writerow([
            str(log.date), log.meal_type, log.food_name, log.quantity_g,
            round(n.get("calories", 0)), round(n.get("protein", 0), 1),
            round(n.get("carbs", 0), 1), round(n.get("fat", 0), 1),
            round(n.get("fiber", 0), 1), round(n.get("sugar", 0), 1)
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=chefbuilder_food_log_{today}.csv"}
    )


# ─────────────────────────────────────────────────────────────────────────────
#  API — SAVED RECIPES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/recipes/saved", methods=["GET", "POST"])
def saved_recipes_api():
    if request.method == "GET":
        recipes = get_saved_recipes()
        return jsonify([{
            "id": r.id, "name": r.name, "content": r.content,
            "source": r.source, "created_at": r.created_at.strftime("%b %d, %Y")
        } for r in recipes])
    data = request.json
    if not data or not data.get("name") or not data.get("content"):
        return jsonify({"error": "name and content required"}), 400
    recipe_id = add_saved_recipe(
        name=data["name"].strip(),
        content=data["content"].strip(),
        source=data.get("source", "ai_coach"),
    )
    return jsonify({"success": True, "id": recipe_id})


@app.route("/api/recipes/saved/<recipe_id>", methods=["DELETE"])
def delete_saved_recipe_route(recipe_id):
    delete_saved_recipe(recipe_id)
    return jsonify({"success": True})


@app.route("/api/chat/clear", methods=["DELETE"])
def clear_chat():
    clear_chat_messages()
    return jsonify({"success": True})


# ─────────────────────────────────────────────────────────────────────────────
#  TEMPLATE FILTERS & CONTEXT
# ─────────────────────────────────────────────────────────────────────────────

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

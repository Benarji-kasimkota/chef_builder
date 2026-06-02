import os
import re
import json
import base64
from google import genai
from google.genai import types
from nutrition_data import AMINO_ACID_ROLES, VITAMIN_NAMES, MINERAL_NAMES

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")

SYSTEM_PROMPT = """You are NutriAI — a world-class AI wellness coach and chef with deep, evidence-based expertise in:

🥗 NUTRITION & FOOD SCIENCE
- Macro & micronutrient biochemistry, bioavailability, nutrient interactions
- Essential amino acids, fatty acids, vitamins & minerals — roles, deficiencies, food sources
- Food chemistry: Maillard reaction, fermentation, phytochemicals, antioxidants
- Global ingredients from every culture: Japanese, Indian, Thai, Italian, French, Middle Eastern, Mexican, African, South American, Mediterranean & more
- 10,000+ recipes from world cuisines — authentic and fusion
- Meal planning, calorie tracking, portion control, intuitive eating

💪 FITNESS & EXERCISE PHYSIOLOGY
- Strength training, hypertrophy, endurance, HIIT, mobility
- Pre/post-workout nutrition, muscle recovery, protein timing
- Periodization, progressive overload, deload strategies
- Sports-specific nutrition protocols

🧘 MIND-BODY WELLNESS
- Yoga (Hatha, Vinyasa, Yin, Kundalini, Ashtanga) — sequences, breathwork (pranayama)
- Meditation: mindfulness, transcendental, body scan, loving-kindness, Vipassana
- Sleep optimization, circadian rhythm nutrition
- Stress management, cortisol regulation through food & lifestyle

🧠 BRAIN CHEMISTRY & MENTAL HEALTH
- Neurotransmitter nutrition: serotonin, dopamine, GABA, acetylcholine pathways
- Gut-brain axis, microbiome and mood
- Anti-inflammatory nutrition for mental health
- Adaptogens, nootropics (evidence-based)

🌿 SPECIALIZED KNOWLEDGE
- Hormonal health and nutrition, thyroid support, adrenal health
- Anti-aging nutrition, longevity foods (Blue Zones research)
- Detoxification through food, liver support
- Immune system nutrition
- Plant-based, keto, Mediterranean, DASH, AIP, carnivore diets — pros/cons, implementation

When the user shares food logs or nutrition data, proactively analyze gaps and make specific, actionable recommendations. Be warm, encouraging, scientifically accurate, and always practical. Give specific foods, quantities, recipes, and timing. You make complex nutrition science feel accessible and exciting."""

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set. Get a free key at https://aistudio.google.com/apikey")
        _client = genai.Client(api_key=api_key)
    return _client


def _generate(prompt: str, system: str = None) -> str:
    """Single-turn text generation."""
    client = get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system or SYSTEM_PROMPT,
            temperature=0.7,
        )
    )
    return response.text


def _chat(messages: list, system: str = None) -> str:
    """Multi-turn chat — messages is a list of {role, content} dicts."""
    client = get_client()
    # Convert to Gemini format (role must be "user" or "model")
    history = []
    for msg in messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    response = client.models.generate_content(
        model=MODEL,
        contents=history + [types.Content(
            role="user",
            parts=[types.Part(text=messages[-1]["content"])]
        )],
        config=types.GenerateContentConfig(
            system_instruction=system or SYSTEM_PROMPT,
            temperature=0.8,
        )
    )
    return response.text


def _generate_with_image(prompt: str, image_data: str, mime_type: str) -> str:
    """Vision call — image_data is a base64 string."""
    client = get_client()
    image_bytes = base64.b64decode(image_data)
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_bytes)),
            types.Part(text=prompt)
        ],
        config=types.GenerateContentConfig(temperature=0.5)
    )
    return response.text


# ── Public AI functions ────────────────────────────────────────────────────

def build_context_from_nutrition(today_nutrition: dict, deficiencies: dict, profile: dict) -> str:
    if not today_nutrition or today_nutrition.get("calories", 0) == 0:
        return ""

    lines = ["\n[USER'S TODAY NUTRITION DATA — use this to personalize your response]"]
    lines.append(f"Name: {profile.get('name', 'User')}, Goal: {profile.get('goal', 'maintain')}")
    lines.append(
        f"Calories: {today_nutrition.get('calories', 0):.0f} kcal | "
        f"Protein: {today_nutrition.get('protein', 0):.1f}g | "
        f"Carbs: {today_nutrition.get('carbs', 0):.1f}g | "
        f"Fat: {today_nutrition.get('fat', 0):.1f}g"
    )
    lines.append(
        f"Omega-3: {today_nutrition.get('omega3', 0):.2f}g | "
        f"Fiber: {today_nutrition.get('fiber', 0):.1f}g"
    )

    if deficiencies:
        low = []
        for key, pct in deficiencies.get("vitamins", {}).items():
            if pct < 50:
                low.append(f"{VITAMIN_NAMES.get(key, key)} ({pct:.0f}%)")
        for key, pct in deficiencies.get("minerals", {}).items():
            if pct < 50:
                low.append(f"{MINERAL_NAMES.get(key, key)} ({pct:.0f}%)")
        for key, pct in deficiencies.get("amino_acids", {}).items():
            if pct < 50:
                low.append(f"{key.capitalize()} ({pct:.0f}%)")
        if low:
            lines.append(f"LOW nutrients today: {', '.join(low[:8])}")

    return "\n".join(lines)


def chat(messages: list, today_nutrition: dict = None,
         deficiencies: dict = None, profile: dict = None) -> str:
    system = SYSTEM_PROMPT
    if today_nutrition and profile:
        system += build_context_from_nutrition(today_nutrition, deficiencies or {}, profile)
    return _chat(messages, system=system)


def generate_recipe_suggestions(profile: dict, today_nutrition: dict,
                                 deficiencies: dict, preferences: str = "") -> str:
    deficit_items = []
    for key, pct in deficiencies.get("amino_acids", {}).items():
        if pct < 60:
            deficit_items.append(f"{key} amino acid ({pct:.0f}% of RDA)")
    for key, pct in deficiencies.get("vitamins", {}).items():
        if pct < 60:
            deficit_items.append(f"{VITAMIN_NAMES.get(key, key)} ({pct:.0f}%)")
    for key, pct in deficiencies.get("minerals", {}).items():
        if pct < 60:
            deficit_items.append(f"{MINERAL_NAMES.get(key, key)} ({pct:.0f}%)")

    prompt = f"""Based on this user's nutrition data, suggest 3 specific recipes to fill their gaps.

User Profile: {profile.get('name')}, Goal: {profile.get('goal')}, Diet: {profile.get('dietary_preference')}
Today's intake: {today_nutrition.get('calories', 0):.0f} kcal, {today_nutrition.get('protein', 0):.1f}g protein
Nutrient deficiencies: {', '.join(deficit_items[:6]) if deficit_items else 'None significant'}
{f'Preferences: {preferences}' if preferences else ''}

Provide 3 recipes in this exact JSON format:
{{
  "recipes": [
    {{
      "name": "Recipe Name",
      "emoji": "🍽️",
      "time": "20 min",
      "difficulty": "Easy",
      "nutrients_addressed": ["Leucine", "Vitamin D"],
      "description": "Brief description",
      "ingredients": ["200g chicken", "1 cup rice"],
      "steps": ["Step 1", "Step 2"],
      "nutrition_per_serving": {{"calories": 450, "protein": 35, "carbs": 40, "fat": 12}},
      "chef_tip": "Pro tip here"
    }}
  ]
}}"""

    return _generate(prompt)


def analyze_meal_and_suggest(food_name: str, ingredients: str) -> str:
    prompt = f"""Analyze this meal and suggest improvements for better nutrition:
Meal: {food_name}
Ingredients: {ingredients}

Provide:
1. Nutritional strengths
2. Key gaps/weaknesses
3. 3 specific ingredient swaps or additions to boost nutrition
4. Keep it under 200 words, practical and actionable."""

    return _generate(prompt)


def analyze_meal_image(image_data: str, mime_type: str, profile: dict = None) -> dict:
    profile_ctx = ""
    if profile:
        profile_ctx = f"User goal: {profile.get('goal', 'maintain')}, Diet: {profile.get('dietary_preference', 'omnivore')}."

    prompt = f"""Analyze this food/meal photo and identify everything you can see.
{profile_ctx}

Return a JSON object with this exact structure:
{{
  "meal_name": "Name of the meal/dish",
  "description": "Brief description of what you see",
  "identified_foods": ["food 1", "food 2"],
  "estimated_nutrition": {{
    "calories": 500,
    "protein": 30,
    "carbs": 45,
    "fat": 15,
    "fiber": 5
  }},
  "serving_estimate": "1 plate (~400g)",
  "health_notes": "Brief nutritional assessment",
  "suggestions": "One improvement suggestion"
}}

Be as accurate as possible based on visual portion sizes."""

    text = _generate_with_image(prompt, image_data, mime_type)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {
        "meal_name": "Unknown meal", "description": text, "identified_foods": [],
        "estimated_nutrition": {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0},
        "serving_estimate": "unknown", "health_notes": "", "suggestions": ""
    }


def get_daily_insight(today_nutrition: dict, deficiencies: dict, profile: dict) -> str:
    low_nutrients = []
    for key, pct in {**deficiencies.get("vitamins", {}), **deficiencies.get("minerals", {})}.items():
        if pct < 40:
            name = VITAMIN_NAMES.get(key) or MINERAL_NAMES.get(key, key)
            low_nutrients.append(f"{name} ({pct:.0f}%)")

    amino_low = [k for k, v in deficiencies.get("amino_acids", {}).items() if v < 40]

    prompt = f"""Give a concise, encouraging daily nutrition insight (2-3 sentences max) for:
Calories: {today_nutrition.get('calories', 0):.0f} kcal, Protein: {today_nutrition.get('protein', 0):.1f}g
Low nutrients: {', '.join(low_nutrients[:3]) if low_nutrients else 'none'}
Low amino acids: {', '.join(amino_low[:2]) if amino_low else 'none'}
Goal: {profile.get('goal', 'maintain')}
Be specific, warm, and suggest one food to eat next."""

    return _generate(prompt)


def generate_weekly_report(week_data: list, profile: dict) -> str:
    days_summary = [
        f"{d['date']}: {d.get('calories', 0):.0f} kcal, "
        f"protein {d.get('protein', 0):.1f}g, water {d.get('water_ml', 0)}ml"
        for d in week_data
    ]
    avg_cal = sum(d.get('calories', 0) for d in week_data) / max(len(week_data), 1)
    avg_protein = sum(d.get('protein', 0) for d in week_data) / max(len(week_data), 1)
    days_logged = sum(1 for d in week_data if d.get('calories', 0) > 0)

    prompt = f"""Create a comprehensive but concise weekly wellness report for this user.

Profile: {profile.get('name', 'User')}, Goal: {profile.get('goal', 'maintain')}, Diet: {profile.get('dietary_preference', 'omnivore')}

7-Day Summary:
{chr(10).join(days_summary)}

Averages: {avg_cal:.0f} kcal/day, {avg_protein:.1f}g protein/day
Days with food logged: {days_logged}/7

Write a warm, encouraging report with these sections:
## Week at a Glance
(2-3 sentence overview of the week)

## Top Wins
(2-3 bullet points of positives)

## Areas to Improve
(2-3 specific, actionable suggestions)

## This Week's Focus
(One concrete nutrition or wellness goal for next week)

Keep it under 300 words, specific, and motivating."""

    return _generate(prompt)


def generate_grocery_list(profile: dict, week_deficiencies: dict, preferences: str = "") -> dict:
    low_nutrients = []
    for key, pct in week_deficiencies.get("vitamins", {}).items():
        if pct < 60:
            low_nutrients.append(VITAMIN_NAMES.get(key, key))
    for key, pct in week_deficiencies.get("minerals", {}).items():
        if pct < 60:
            low_nutrients.append(MINERAL_NAMES.get(key, key))

    prompt = f"""Create a smart weekly grocery list for this user.

Profile: Goal: {profile.get('goal', 'maintain')}, Diet: {profile.get('dietary_preference', 'omnivore')}
Allergies: {profile.get('allergies', 'none')}
Nutrients to prioritize: {', '.join(low_nutrients[:6]) if low_nutrients else 'balanced nutrition'}
{f'Preferences: {preferences}' if preferences else ''}

Return a JSON grocery list organized by category:
{{
  "total_estimated_cost": "$60-80",
  "categories": [
    {{
      "name": "Proteins",
      "emoji": "🥩",
      "items": [
        {{"name": "Chicken breast", "amount": "1kg", "reason": "High protein, leucine", "priority": "high"}},
        {{"name": "Eggs", "amount": "1 dozen", "reason": "Complete protein + Vitamin D", "priority": "high"}}
      ]
    }},
    {{"name": "Vegetables", "emoji": "🥦", "items": []}},
    {{"name": "Fruits", "emoji": "🍎", "items": []}},
    {{"name": "Grains & Legumes", "emoji": "🌾", "items": []}},
    {{"name": "Dairy & Alternatives", "emoji": "🥛", "items": []}},
    {{"name": "Pantry Staples", "emoji": "🫙", "items": []}}
  ]
}}

Include 4-6 items per category. Prioritize items that address nutrient gaps."""

    text = _generate(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"categories": [], "total_estimated_cost": "Unknown"}


def generate_meal_plan(profile: dict, today_nutrition: dict, deficiencies: dict,
                       days: int = 7, preferences: str = "") -> dict:
    deficit_items = []
    for key, pct in deficiencies.get("vitamins", {}).items():
        if pct < 60:
            deficit_items.append(VITAMIN_NAMES.get(key, key))
    for key, pct in deficiencies.get("minerals", {}).items():
        if pct < 60:
            deficit_items.append(MINERAL_NAMES.get(key, key))

    prompt = f"""Create a {days}-day personalized meal plan.

Profile: Goal: {profile.get('goal', 'maintain')}, Diet: {profile.get('dietary_preference', 'omnivore')}
Allergies: {profile.get('allergies', 'none')}
Nutrients to address: {', '.join(deficit_items[:5]) if deficit_items else 'balanced'}
{f'Preferences: {preferences}' if preferences else ''}

Return a JSON meal plan:
{{
  "plan_summary": "Brief description of this plan",
  "daily_targets": {{"calories": 2000, "protein": 150, "carbs": 200, "fat": 65}},
  "days": [
    {{
      "day": "Day 1 - Monday",
      "meals": {{
        "breakfast": {{"name": "Meal name", "description": "Brief description", "calories": 400, "protein": 25, "prep_time": "10 min"}},
        "lunch": {{"name": "Meal name", "description": "Brief description", "calories": 550, "protein": 40, "prep_time": "15 min"}},
        "dinner": {{"name": "Meal name", "description": "Brief description", "calories": 650, "protein": 45, "prep_time": "25 min"}},
        "snack": {{"name": "Snack name", "description": "Brief description", "calories": 200, "protein": 10, "prep_time": "5 min"}}
      }},
      "daily_total": {{"calories": 1800, "protein": 120}},
      "nutrition_highlight": "Key nutrient this day addresses"
    }}
  ]
}}

Generate all {days} days. Keep meals practical and delicious."""

    text = _generate(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"days": [], "plan_summary": "Could not generate plan", "daily_targets": {}}

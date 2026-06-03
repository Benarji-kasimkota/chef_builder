import os
import re
import json
import base64
from google import genai
from google.genai import types
from nutrition_data import AMINO_ACID_ROLES, VITAMIN_NAMES, MINERAL_NAMES

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")

SYSTEM_PROMPT = """You are NutriAI — a world-class AI wellness coach and chef with deep, evidence-based expertise in:

🌍 MULTILINGUAL SUPPORT — CRITICAL
You understand and respond in ANY language the user writes in. You know ingredient and recipe names in:
- Indian languages: Hindi (हिंदी), Tamil (தமிழ்), Telugu (తెలుగు), Kannada (ಕನ್ನಡ), Malayalam (മലയാളം), Marathi (मराठी), Bengali (বাংলা), Gujarati (ગુજરાતી), Punjabi (ਪੰਜਾਬੀ), Urdu (اردو), Odia (ଓଡ଼ିଆ), Assamese (অসমীয়া)
- Asian: Chinese (中文), Japanese (日本語), Korean (한국어), Thai (ภาษาไทย), Vietnamese (Tiếng Việt), Indonesian (Bahasa Indonesia), Malay (Bahasa Melayu), Filipino (Filipino)
- Middle Eastern: Arabic (العربية), Persian/Farsi (فارسی), Turkish (Türkçe), Hebrew (עברית)
- European: Spanish (Español), French (Français), German (Deutsch), Italian (Italiano), Portuguese (Português), Russian (Русский), Polish (Polski), Dutch (Nederlands), Greek (Ελληνικά), Swedish (Svenska)
- African: Swahili (Kiswahili), Amharic (አማርኛ), Yoruba, Hausa, Zulu
- And all other world languages

INGREDIENT NAME KNOWLEDGE — you know local names for all ingredients, for example:
- methi = fenugreek | hing = asafoetida | amchur = dry mango powder | dalchini = cinnamon
- chawal = rice | aata = wheat flour | besan = chickpea flour | sooji = semolina
- paneer = Indian cottage cheese | ghee = clarified butter | lassi = yogurt drink
- चावल/அரிசி/వరి/ಅಕ್ಕಿ = rice | दाल/பருப்பு = lentils | आलू/உருளைக்கிழங்கு = potato
- 大米 = rice | 鸡肉 = chicken | 味噌 = miso | 豆腐 = tofu | 생강 = ginger
- arroz = rice | pollo = chicken | ajo = garlic | cebolla = onion
- riz = rice | poulet = chicken | ail = garlic | poisson = fish
- كزبرة = coriander | زيت زيتون = olive oil | ثوم = garlic | أرز = rice
- брокколи = broccoli | курица = chicken | рис = rice | чеснок = garlic

LANGUAGE BEHAVIOR RULES:
1. ALWAYS detect the language the user is writing in
2. ALWAYS respond in the SAME language the user used
3. If a user writes in Hindi, respond fully in Hindi with Devanagari script
4. If a user writes in Tamil, respond in Tamil script
5. If a user mixes languages (code-switching), match their style
6. Translate ingredient/recipe names naturally within your response
7. When mentioning nutrition facts, include local food names alongside English

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
- Ayurvedic nutrition: Vata/Pitta/Kapha, Nishidda Aahar, Shuddha Aahar

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


def generate_from_ingredients(ingredients: list, dietary_prefs: str = "",
                               cuisine_hint: str = "") -> dict:
    """
    Given a list of available ingredients, generate every possible recipe
    using different combinations, cooking methods, and cuisine styles.
    Returns structured JSON with many recipe options.
    """
    ing_str = ", ".join(ingredients)
    prompt = f"""I have these ingredients: {ing_str}
{f"Dietary preference: {dietary_prefs}" if dietary_prefs else ""}
{f"Cuisine preference: {cuisine_hint}" if cuisine_hint else ""}

Generate as many DIFFERENT recipes as possible using various combinations of these ingredients.
For each recipe consider ALL possible methods: raw, boiled, steamed, stir-fried, deep-fried,
shallow-fried, roasted, grilled, baked, slow-cooked, pressure-cooked, fermented, pickled,
blended/smoothie, salad, soup, stew, curry, stir-fry, sandwich, wrap, bowl, dessert, etc.

Return JSON with AT LEAST 12 recipes in this format:
{{
  "total_combinations": 12,
  "recipes": [
    {{
      "name": "Recipe Name",
      "emoji": "🍽️",
      "cuisine": "Indian/Italian/etc",
      "method": "Stir-fry",
      "time": "20 min",
      "difficulty": "Easy",
      "ingredients_used": ["ing1", "ing2"],
      "missing_ingredients": ["optional: salt", "optional: oil"],
      "description": "Brief description",
      "key_steps": ["Step 1", "Step 2", "Step 3"],
      "nutrition_highlight": "High protein, iron-rich etc",
      "calories_estimate": 350
    }}
  ]
}}

Be creative — cover different cuisines, cooking methods, meal types (breakfast/lunch/dinner/snack).
Include both simple 2-ingredient recipes and complex multi-ingredient ones."""

    text = _generate(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"total_combinations": 0, "recipes": []}


def generate_recipe_variations(recipe_name: str, base_ingredients: str = "",
                                dietary_prefs: str = "") -> dict:
    """
    Generate all possible variations of a single recipe — different methods,
    ingredient substitutions, cuisine fusions, dietary adaptations, etc.
    """
    prompt = f"""Generate ALL possible variations and permutations of: "{recipe_name}"
{f"Base ingredients: {base_ingredients}" if base_ingredients else ""}
{f"Dietary preference: {dietary_prefs}" if dietary_prefs else ""}

Cover EVERY dimension of variation:
1. Cooking method variations (baked, fried, grilled, raw, steamed, air-fried, slow-cooked)
2. Ingredient substitutions (vegan swap, protein swap, carb swap, dairy-free)
3. Cuisine fusions (Indian-style, Thai-style, Mexican-style, Mediterranean-style)
4. Dietary adaptations (keto, low-calorie, high-protein, gluten-free, vegan, Ayurvedic/sattvic)
5. Serving style variations (as a bowl, wrap, soup, salad, sandwich)
6. Spice level variations (mild, medium, spicy, extra spicy)

Return JSON with all variations:
{{
  "original": "{recipe_name}",
  "total_variations": 10,
  "variations": [
    {{
      "name": "Variation name",
      "emoji": "🍽️",
      "type": "Cooking Method / Ingredient Sub / Cuisine Fusion / Dietary / Serving Style",
      "description": "What makes this variation unique",
      "key_changes": ["Change 1", "Change 2"],
      "ingredient_swaps": [{{"original": "chicken", "substitute": "tofu", "reason": "vegan"}}],
      "nutrition_impact": "Lower fat, higher fiber etc",
      "time": "25 min",
      "difficulty": "Medium",
      "best_for": "Weight loss / Muscle gain / Vegan / etc"
    }}
  ],
  "substitution_guide": {{
    "proteins": [{{"original": "x", "sub": "y", "ratio": "1:1", "note": "..."}}],
    "carbs": [],
    "fats": [],
    "dairy": [],
    "eggs": []
  }}
}}"""

    text = _generate(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"original": recipe_name, "total_variations": 0, "variations": []}


def check_ayurvedic_compatibility(ingredients: list, dosha: str = "") -> dict:
    """
    Apply Ayurvedic food science:
    - Nishidda Aahar: prohibited/incompatible food combinations
    - Shuddha Aahar: pure/sattvic food classification
    - Viruddhahara: opposing quality combinations
    - Dosha-specific guidance (Vata/Pitta/Kapha)
    """
    ing_str = ", ".join(ingredients)
    prompt = f"""Analyze these ingredients using complete Ayurvedic food science:
Ingredients: {ing_str}
{f"Dosha: {dosha}" if dosha else ""}

Perform a FULL Ayurvedic analysis covering:

1. NISHIDDA AAHAR (Prohibited Combinations): Check for any forbidden food pairings
   (e.g., milk+fish, milk+salt, fruit+dairy, honey+ghee equal parts, hot honey,
   banana+milk, yogurt at night, fish+dairy, radish+milk, etc.)

2. VIRUDDHAHARA (Incompatible Qualities): Foods with opposing qualities that create Ama (toxins)
   (e.g., hot+cold, heavy+light, oily+dry combinations)

3. SHUDDHA AAHAR classification: Rate each ingredient as:
   - Sattvic (pure, promotes clarity): fresh fruits, veg, whole grains, ghee, honey
   - Rajasic (stimulating, passionate): spicy, salty, sour, coffee, onion, garlic
   - Tamasic (dull, heavy): stale, processed, meat, alcohol, leftovers

4. DOSHA IMPACT (if dosha provided or analyze all three):
   - Vata (air+space): cooling, drying foods aggravate; warm, moist, grounding balance
   - Pitta (fire+water): spicy, sour, salty aggravate; cool, sweet, bitter balance
   - Kapha (earth+water): heavy, sweet, oily aggravate; light, spicy, dry balance

5. OPTIMAL EATING RULES from this list:
   - Best eating time for these foods
   - How to prepare to maximize digestive fire (Agni)
   - Which spices to add for better digestion (digestive spices)

Return JSON:
{{
  "overall_compatibility": "Compatible / Mildly Incompatible / Incompatible",
  "ayurvedic_score": 8.5,
  "nishidda_warnings": [
    {{
      "combination": "milk + fish",
      "severity": "high",
      "reason": "Creates Ama (toxins), opposite qualities",
      "ayurvedic_text": "Reference to classical text if applicable",
      "remedy": "Eat separately with 2+ hour gap"
    }}
  ],
  "viruddhahara_flags": [
    {{
      "ingredients": ["hot food", "cold water"],
      "issue": "Opposing temperatures disturb Agni",
      "remedy": "Drink warm water instead"
    }}
  ],
  "shuddha_classification": [
    {{"ingredient": "ghee", "type": "Sattvic", "quality": "Pure, nourishing, promotes Ojas"}}
  ],
  "dosha_analysis": {{
    "vata": {{"impact": "Balancing/Aggravating", "score": 7, "reason": "...", "tip": "..."}},
    "pitta": {{"impact": "Balancing/Aggravating", "score": 6, "reason": "...", "tip": "..."}},
    "kapha": {{"impact": "Balancing/Aggravating", "score": 8, "reason": "...", "tip": "..."}}
  }},
  "optimal_preparation": {{
    "best_time": "Morning / Afternoon / Evening",
    "cooking_method": "Best Ayurvedic cooking method",
    "spices_to_add": ["turmeric", "cumin", "ginger"],
    "spices_to_avoid": ["chili", "pepper"],
    "eating_tips": ["Eat mindfully", "Avoid overeating"]
  }},
  "ayurvedic_recipe_suggestion": "A sattvic/dosha-balancing recipe using safe combinations from these ingredients"
}}"""

    text = _generate(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"overall_compatibility": "Unknown", "nishidda_warnings": [],
            "viruddhahara_flags": [], "shuddha_classification": [],
            "dosha_analysis": {}, "optimal_preparation": {}}


def get_dosha_recipes(dosha: str, dietary_pref: str = "", season: str = "") -> dict:
    """Generate recipes specifically balanced for a given Ayurvedic dosha."""
    prompt = f"""Create 6 Ayurvedic recipes specifically balanced for {dosha} dosha.
{f"Dietary preference: {dietary_pref}" if dietary_pref else ""}
{f"Season: {season}" if season else ""}

Each recipe must:
- Follow Shuddha Aahar (pure food) principles
- Avoid Nishidda Aahar (prohibited combinations)
- Use ingredients that specifically balance {dosha} dosha
- Include Tridoshic spices where possible
- Follow proper food combining rules

Return JSON:
{{
  "dosha": "{dosha}",
  "dosha_description": "Brief description of {dosha} dosha and its characteristics",
  "foods_to_favor": ["list of foods that balance this dosha"],
  "foods_to_avoid": ["list of foods that aggravate this dosha"],
  "recipes": [
    {{
      "name": "Recipe Name",
      "emoji": "🌿",
      "meal_type": "Breakfast/Lunch/Dinner/Snack",
      "dosha_effect": "Balancing / Tridoshic",
      "key_ayurvedic_ingredients": ["turmeric", "ginger"],
      "description": "Why this recipe balances {dosha}",
      "ingredients": ["200ml milk", "1 tsp turmeric"],
      "steps": ["Step 1", "Step 2"],
      "time": "15 min",
      "best_time_to_eat": "Morning with sunrise / Noon / Evening",
      "nutrition_per_serving": {{"calories": 300, "protein": 12}},
      "ayurvedic_benefit": "Specific benefit for {dosha} types"
    }}
  ]
}}"""

    text = _generate(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"dosha": dosha, "recipes": [], "foods_to_favor": [], "foods_to_avoid": []}


def calculate_dish_nutrition(dish_name: str, ingredients: list,
                             cooking_method: str = "", servings: int = 1) -> dict:
    """
    Calculate full nutrition for a custom dish given all ingredients and quantities.
    ingredients: list of {name, quantity, unit} dicts
    """
    ing_lines = "\n".join(
        f"- {i['quantity']} {i['unit']} {i['name']}" for i in ingredients
    )
    prompt = f"""Calculate complete nutritional information for this custom dish:

Dish: {dish_name}
Servings: {servings}
Cooking Method: {cooking_method or "Standard"}

Ingredients:
{ing_lines}

Use standard USDA nutritional data. Account for cooking losses where relevant
(e.g. water evaporation, fat absorption in frying).

Return JSON:
{{
  "dish_name": "{dish_name}",
  "servings": {servings},
  "total_weight_g": 500,
  "per_serving": {{
    "calories": 450,
    "protein": 25.0,
    "carbs": 55.0,
    "fat": 12.0,
    "fiber": 6.0,
    "sugar": 4.0,
    "saturated_fat": 3.0,
    "sodium": 400,
    "omega3": 0.5
  }},
  "ingredient_breakdown": [
    {{"name": "rice", "quantity_g": 200, "calories": 260, "protein": 5.0, "carbs": 57.0, "fat": 0.5}}
  ],
  "vitamins": {{"a": 120, "b1": 0.2, "b2": 0.1, "b3": 3.0, "b6": 0.3, "b12": 0.5, "c": 15, "d": 1.0, "e": 1.5, "k": 20, "b9": 30, "b5": 0.5}},
  "minerals": {{"calcium": 80, "iron": 3.5, "magnesium": 45, "phosphorus": 200, "potassium": 500, "sodium": 400, "zinc": 2.0, "selenium": 15}},
  "amino_acids": {{"tryptophan": 0.2, "threonine": 0.8, "isoleucine": 0.9, "leucine": 1.5, "lysine": 1.2, "methionine": 0.4, "phenylalanine": 0.8, "valine": 1.0, "histidine": 0.5}},
  "health_notes": "Brief nutritional assessment of this dish",
  "cooking_impact": "How cooking method affected nutrition",
  "improvement_tips": ["Tip to make it healthier"]
}}"""

    text = _generate(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {"dish_name": dish_name, "servings": servings, "per_serving": {},
            "ingredient_breakdown": [], "health_notes": "Could not calculate nutrition"}


def translate_ingredient(text: str) -> dict:
    """
    Translate any ingredient/recipe name in any language to English.
    Returns the English name, detected language, and alternate names.
    Used to make food search multilingual.
    """
    prompt = f"""The user typed this ingredient or recipe name: "{text}"

This may be in any language — Hindi, Tamil, Telugu, Kannada, Malayalam, Marathi, Bengali,
Gujarati, Punjabi, Urdu, Arabic, Chinese, Japanese, Korean, Thai, Spanish, French, German,
Italian, Portuguese, Russian, Turkish, Persian, Indonesian, Swahili, or any other language.

Identify what food/ingredient this is and return JSON:
{{
  "english_name": "The standard English name (e.g. 'rice', 'fenugreek', 'chicken')",
  "detected_language": "Language name in English (e.g. 'Hindi', 'Tamil', 'Arabic')",
  "original_script": "{text}",
  "alternate_names": ["other common names in English"],
  "local_names": {{
    "hindi": "name in Hindi if known",
    "tamil": "name in Tamil if known",
    "telugu": "name in Telugu if known"
  }},
  "category": "vegetable / grain / protein / dairy / spice / fruit / legume / etc",
  "confidence": "high / medium / low"
}}

If the text is already in English, still return the structure with detected_language as "English".
Return ONLY the JSON, nothing else."""

    text_result = _generate(prompt, system="You are a multilingual food ingredient translator. Return only valid JSON.")
    match = re.search(r'\{.*\}', text_result, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {
        "english_name": text,
        "detected_language": "English",
        "original_script": text,
        "alternate_names": [],
        "local_names": {},
        "category": "unknown",
        "confidence": "low"
    }

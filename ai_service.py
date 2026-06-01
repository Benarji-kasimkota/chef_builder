import os
import anthropic
from nutrition_data import AMINO_ACID_ROLES, VITAMIN_NAMES, MINERAL_NAMES

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
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def build_context_from_nutrition(today_nutrition: dict, deficiencies: dict, profile: dict) -> str:
    """Build a context string from the user's nutrition data to inject into chat."""
    if not today_nutrition or today_nutrition.get("calories", 0) == 0:
        return ""

    lines = [f"\n[USER'S TODAY NUTRITION DATA — use this to personalize your response]"]
    lines.append(f"Name: {profile.get('name', 'User')}, Goal: {profile.get('goal', 'maintain')}")
    lines.append(f"Calories: {today_nutrition.get('calories', 0):.0f} kcal | "
                 f"Protein: {today_nutrition.get('protein', 0):.1f}g | "
                 f"Carbs: {today_nutrition.get('carbs', 0):.1f}g | "
                 f"Fat: {today_nutrition.get('fat', 0):.1f}g")
    lines.append(f"Omega-3: {today_nutrition.get('omega3', 0):.2f}g | "
                 f"Fiber: {today_nutrition.get('fiber', 0):.1f}g")

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
    """Send chat messages to Claude and return response."""
    client = get_client()
    system = SYSTEM_PROMPT
    if today_nutrition and profile:
        system += build_context_from_nutrition(today_nutrition, deficiencies or {}, profile)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system,
        messages=messages
    )
    return response.content[0].text


def generate_recipe_suggestions(profile: dict, today_nutrition: dict,
                                 deficiencies: dict, preferences: str = "") -> str:
    """Generate personalized recipe suggestions based on nutrition gaps."""
    client = get_client()
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

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def analyze_meal_and_suggest(food_name: str, ingredients: str) -> str:
    """Analyze a meal and suggest improvements."""
    client = get_client()
    prompt = f"""Analyze this meal and suggest improvements for better nutrition:
Meal: {food_name}
Ingredients: {ingredients}

Provide:
1. Nutritional strengths
2. Key gaps/weaknesses
3. 3 specific ingredient swaps or additions to boost nutrition
4. Keep it under 200 words, practical and actionable."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def get_daily_insight(today_nutrition: dict, deficiencies: dict, profile: dict) -> str:
    """Generate a short daily nutrition insight."""
    client = get_client()
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

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

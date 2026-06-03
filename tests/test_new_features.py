"""
Tests for features added after the original test suite:
  - /api/translate  (multilingual ingredient translation)
  - /api/recipes/from-ingredients  (fridge → all possible recipes)
  - /api/recipes/variations  (all ways to make a dish)
  - /api/recipes/ayurvedic-check  (Nishidda Aahar / dosha analysis)
  - /api/recipes/dosha  (dosha-balanced recipe generation)
  - SQLite WAL mode is active
  - New AI service functions (translate_ingredient, generate_from_ingredients,
    generate_recipe_variations, check_ayurvedic_compatibility, get_dosha_recipes)
"""
import json
import pytest
from unittest.mock import patch

from tests.conftest import CHICKEN_200G


# ── AI mock helpers (Gemini-style) ────────────────────────────────────────
def _patch_gen(text="OK"):
    return patch("ai_service._generate", return_value=text)


# ══════════════════════════════════════════════════════════════════════════
# /api/translate
# ══════════════════════════════════════════════════════════════════════════

class TestTranslate:

    def test_empty_text_returns_400(self, client):
        r = client.post("/api/translate", json={"text": ""})
        assert r.status_code == 400

    def test_missing_text_returns_400(self, client):
        r = client.post("/api/translate", json={})
        assert r.status_code == 400

    def test_english_word_returns_200(self, client):
        mock_json = json.dumps({
            "english_name": "rice",
            "detected_language": "English",
            "original_script": "rice",
            "alternate_names": ["white rice"],
            "local_names": {"hindi": "चावल", "tamil": "அரிசி"},
            "category": "grain",
            "confidence": "high"
        })
        with _patch_gen(mock_json):
            r = client.post("/api/translate", json={"text": "rice"})
        assert r.status_code == 200

    def test_response_has_english_name(self, client):
        mock_json = json.dumps({
            "english_name": "fenugreek",
            "detected_language": "Hindi",
            "original_script": "मेथी",
            "alternate_names": ["methi"],
            "local_names": {},
            "category": "spice",
            "confidence": "high"
        })
        with _patch_gen(mock_json):
            r = client.post("/api/translate", json={"text": "मेथी"})
        data = r.get_json()
        assert "english_name" in data
        assert data["english_name"] == "fenugreek"

    def test_response_has_detected_language(self, client):
        mock_json = json.dumps({
            "english_name": "rice", "detected_language": "Telugu",
            "original_script": "వరి", "alternate_names": [],
            "local_names": {}, "category": "grain", "confidence": "high"
        })
        with _patch_gen(mock_json):
            r = client.post("/api/translate", json={"text": "వరి"})
        assert r.get_json()["detected_language"] == "Telugu"

    def test_fallback_on_bad_json(self, client):
        """If Gemini returns non-JSON, endpoint returns the original text as english_name."""
        with _patch_gen("Sorry, I cannot translate this."):
            r = client.post("/api/translate", json={"text": "xyz_unknown"})
        assert r.status_code == 200
        data = r.get_json()
        assert "english_name" in data

    def test_response_structure(self, client):
        mock_json = json.dumps({
            "english_name": "chicken", "detected_language": "Arabic",
            "original_script": "دجاج", "alternate_names": ["poultry"],
            "local_names": {}, "category": "protein", "confidence": "high"
        })
        with _patch_gen(mock_json):
            r = client.post("/api/translate", json={"text": "دجاج"})
        data = r.get_json()
        for field in ("english_name", "detected_language", "original_script",
                      "alternate_names", "category", "confidence"):
            assert field in data, f"Missing: {field}"


# ══════════════════════════════════════════════════════════════════════════
# /api/recipes/from-ingredients
# ══════════════════════════════════════════════════════════════════════════

class TestRecipesFromIngredients:

    def test_empty_ingredients_returns_400(self, client):
        r = client.post("/api/recipes/from-ingredients", json={"ingredients": []})
        assert r.status_code == 400

    def test_empty_string_ingredients_returns_400(self, client):
        r = client.post("/api/recipes/from-ingredients", json={"ingredients": ""})
        assert r.status_code == 400

    def test_comma_string_parsed_to_list(self, client):
        """Ingredients can be sent as a comma-separated string."""
        mock = json.dumps({"total_combinations": 1, "recipes": [
            {"name": "Rice Bowl", "emoji": "🍚", "cuisine": "Asian",
             "method": "Boil", "time": "20 min", "difficulty": "Easy",
             "ingredients_used": ["rice"], "missing_ingredients": [],
             "description": "Simple rice bowl", "key_steps": ["Boil rice"],
             "nutrition_highlight": "Carb-rich", "calories_estimate": 300}
        ]})
        with _patch_gen(mock):
            r = client.post("/api/recipes/from-ingredients",
                            json={"ingredients": "rice, egg, onion"})
        assert r.status_code == 200
        data = r.get_json()
        assert "recipes" in data

    def test_returns_recipes_list(self, client):
        mock = json.dumps({"total_combinations": 3, "recipes": [
            {"name": "Dal", "emoji": "🍲", "cuisine": "Indian", "method": "Boil",
             "time": "30 min", "difficulty": "Easy", "ingredients_used": ["lentils", "onion"],
             "missing_ingredients": ["salt"], "description": "Simple dal",
             "key_steps": ["Cook lentils"], "nutrition_highlight": "Protein-rich",
             "calories_estimate": 250},
            {"name": "Omelette", "emoji": "🍳", "cuisine": "French", "method": "Fry",
             "time": "10 min", "difficulty": "Easy", "ingredients_used": ["egg", "onion"],
             "missing_ingredients": [], "description": "Fluffy omelette",
             "key_steps": ["Beat eggs", "Fry"], "nutrition_highlight": "High protein",
             "calories_estimate": 200},
            {"name": "Egg Fried Rice", "emoji": "🍚", "cuisine": "Chinese",
             "method": "Stir-fry", "time": "15 min", "difficulty": "Medium",
             "ingredients_used": ["rice", "egg", "onion"], "missing_ingredients": ["soy sauce"],
             "description": "Classic fried rice", "key_steps": ["Fry rice"],
             "nutrition_highlight": "Balanced", "calories_estimate": 400}
        ]})
        with _patch_gen(mock):
            r = client.post("/api/recipes/from-ingredients",
                            json={"ingredients": ["rice", "egg", "onion", "lentils"]})
        assert r.status_code == 200
        data = r.get_json()
        assert len(data["recipes"]) == 3

    def test_total_combinations_in_response(self, client):
        mock = json.dumps({"total_combinations": 5, "recipes": []})
        with _patch_gen(mock):
            r = client.post("/api/recipes/from-ingredients",
                            json={"ingredients": ["chicken", "rice"]})
        assert r.get_json()["total_combinations"] == 5

    def test_dietary_prefs_accepted(self, client):
        mock = json.dumps({"total_combinations": 2, "recipes": []})
        with _patch_gen(mock):
            r = client.post("/api/recipes/from-ingredients",
                            json={"ingredients": ["tofu", "spinach"],
                                  "dietary_prefs": "vegan",
                                  "cuisine_hint": "Asian"})
        assert r.status_code == 200

    def test_recipe_has_required_fields(self, client):
        mock = json.dumps({"total_combinations": 1, "recipes": [{
            "name": "Khichdi", "emoji": "🍲", "cuisine": "Indian",
            "method": "Pressure-cook", "time": "25 min", "difficulty": "Easy",
            "ingredients_used": ["rice", "lentils"],
            "missing_ingredients": ["ghee", "salt"],
            "description": "Comfort food", "key_steps": ["Cook together"],
            "nutrition_highlight": "Complete protein", "calories_estimate": 350
        }]})
        with _patch_gen(mock):
            r = client.post("/api/recipes/from-ingredients",
                            json={"ingredients": ["rice", "lentils"]})
        recipe = r.get_json()["recipes"][0]
        for field in ("name", "cuisine", "method", "time", "ingredients_used",
                      "calories_estimate"):
            assert field in recipe, f"Missing field: {field}"


# ══════════════════════════════════════════════════════════════════════════
# /api/recipes/variations
# ══════════════════════════════════════════════════════════════════════════

class TestRecipeVariations:

    def test_empty_name_returns_400(self, client):
        r = client.post("/api/recipes/variations", json={"recipe_name": ""})
        assert r.status_code == 400

    def test_missing_name_returns_400(self, client):
        r = client.post("/api/recipes/variations", json={})
        assert r.status_code == 400

    def test_returns_variations_list(self, client):
        mock = json.dumps({
            "original": "Omelette",
            "total_variations": 6,
            "variations": [
                {"name": "Baked Omelette", "emoji": "🍳",
                 "type": "Cooking Method",
                 "description": "Oven-baked version",
                 "key_changes": ["Use oven instead of pan"],
                 "ingredient_swaps": [],
                 "nutrition_impact": "Lower fat",
                 "time": "20 min", "difficulty": "Easy",
                 "best_for": "Low fat"},
                {"name": "Vegan Omelette", "emoji": "🥚",
                 "type": "Dietary Adaptation",
                 "description": "Chickpea flour based",
                 "key_changes": ["Replace eggs with chickpea flour"],
                 "ingredient_swaps": [{"original": "eggs", "substitute": "chickpea flour", "reason": "vegan"}],
                 "nutrition_impact": "Plant-based protein",
                 "time": "15 min", "difficulty": "Easy",
                 "best_for": "Vegan"}
            ],
            "substitution_guide": {
                "proteins": [{"original": "eggs", "sub": "tofu", "ratio": "1:1", "note": "silken tofu"}],
                "dairy": []
            }
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/variations",
                            json={"recipe_name": "Omelette"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["original"] == "Omelette"
        assert len(data["variations"]) == 2

    def test_total_variations_count(self, client):
        mock = json.dumps({"original": "Dal", "total_variations": 8,
                           "variations": [], "substitution_guide": {}})
        with _patch_gen(mock):
            r = client.post("/api/recipes/variations", json={"recipe_name": "Dal"})
        assert r.get_json()["total_variations"] == 8

    def test_substitution_guide_present(self, client):
        mock = json.dumps({
            "original": "Pasta", "total_variations": 5, "variations": [],
            "substitution_guide": {
                "carbs": [{"original": "pasta", "sub": "zucchini noodles", "ratio": "1:1", "note": "keto"}]
            }
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/variations",
                            json={"recipe_name": "Pasta",
                                  "dietary_prefs": "keto"})
        assert "substitution_guide" in r.get_json()

    def test_optional_fields_accepted(self, client):
        mock = json.dumps({"original": "Curry", "total_variations": 4,
                           "variations": [], "substitution_guide": {}})
        with _patch_gen(mock):
            r = client.post("/api/recipes/variations",
                            json={"recipe_name": "Curry",
                                  "base_ingredients": "chicken, onion, tomato",
                                  "dietary_prefs": "high-protein"})
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# /api/recipes/ayurvedic-check
# ══════════════════════════════════════════════════════════════════════════

class TestAyurvedicCheck:

    def test_empty_ingredients_returns_400(self, client):
        r = client.post("/api/recipes/ayurvedic-check", json={"ingredients": []})
        assert r.status_code == 400

    def test_string_ingredients_parsed(self, client):
        mock = json.dumps({
            "overall_compatibility": "Compatible",
            "ayurvedic_score": 9.0,
            "nishidda_warnings": [],
            "viruddhahara_flags": [],
            "shuddha_classification": [
                {"ingredient": "rice", "type": "Sattvic", "quality": "Light, easy to digest"}
            ],
            "dosha_analysis": {},
            "optimal_preparation": {"best_time": "Noon"},
            "ayurvedic_recipe_suggestion": "Simple khichdi"
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/ayurvedic-check",
                            json={"ingredients": "rice, ghee, turmeric"})
        assert r.status_code == 200

    def test_returns_nishidda_warnings(self, client):
        mock = json.dumps({
            "overall_compatibility": "Incompatible",
            "ayurvedic_score": 3.0,
            "nishidda_warnings": [{
                "combination": "milk + fish",
                "severity": "high",
                "reason": "Creates Ama (toxins)",
                "ayurvedic_text": "Charaka Samhita",
                "remedy": "Eat separately with 2+ hour gap"
            }],
            "viruddhahara_flags": [],
            "shuddha_classification": [],
            "dosha_analysis": {},
            "optimal_preparation": {},
            "ayurvedic_recipe_suggestion": ""
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/ayurvedic-check",
                            json={"ingredients": ["milk", "fish"]})
        data = r.get_json()
        assert data["overall_compatibility"] == "Incompatible"
        assert len(data["nishidda_warnings"]) == 1
        assert data["nishidda_warnings"][0]["severity"] == "high"

    def test_ayurvedic_score_in_response(self, client):
        mock = json.dumps({
            "overall_compatibility": "Compatible", "ayurvedic_score": 8.5,
            "nishidda_warnings": [], "viruddhahara_flags": [],
            "shuddha_classification": [], "dosha_analysis": {},
            "optimal_preparation": {}, "ayurvedic_recipe_suggestion": ""
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/ayurvedic-check",
                            json={"ingredients": ["ghee", "turmeric", "ginger"]})
        assert r.get_json()["ayurvedic_score"] == pytest.approx(8.5)

    def test_shuddha_classification_present(self, client):
        mock = json.dumps({
            "overall_compatibility": "Compatible", "ayurvedic_score": 9.0,
            "nishidda_warnings": [], "viruddhahara_flags": [],
            "shuddha_classification": [
                {"ingredient": "ghee", "type": "Sattvic", "quality": "Pure, nourishing"},
                {"ingredient": "garlic", "type": "Rajasic", "quality": "Stimulating"}
            ],
            "dosha_analysis": {}, "optimal_preparation": {},
            "ayurvedic_recipe_suggestion": ""
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/ayurvedic-check",
                            json={"ingredients": ["ghee", "garlic"]})
        classif = r.get_json()["shuddha_classification"]
        assert len(classif) == 2
        types = [c["type"] for c in classif]
        assert "Sattvic" in types
        assert "Rajasic" in types

    def test_dosha_parameter_accepted(self, client):
        mock = json.dumps({
            "overall_compatibility": "Compatible", "ayurvedic_score": 7.0,
            "nishidda_warnings": [], "viruddhahara_flags": [],
            "shuddha_classification": [],
            "dosha_analysis": {
                "pitta": {"impact": "Balancing", "score": 8, "reason": "Cooling", "tip": "Add mint"}
            },
            "optimal_preparation": {}, "ayurvedic_recipe_suggestion": ""
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/ayurvedic-check",
                            json={"ingredients": ["cucumber", "coconut"],
                                  "dosha": "pitta"})
        assert r.status_code == 200
        assert "pitta" in r.get_json()["dosha_analysis"]

    def test_response_has_all_required_keys(self, client):
        mock = json.dumps({
            "overall_compatibility": "Mildly Incompatible", "ayurvedic_score": 6.0,
            "nishidda_warnings": [], "viruddhahara_flags": [],
            "shuddha_classification": [], "dosha_analysis": {},
            "optimal_preparation": {"best_time": "Morning"},
            "ayurvedic_recipe_suggestion": "Add cumin for better digestion"
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/ayurvedic-check",
                            json={"ingredients": ["banana", "yogurt"]})
        data = r.get_json()
        for key in ("overall_compatibility", "ayurvedic_score", "nishidda_warnings",
                    "viruddhahara_flags", "shuddha_classification", "dosha_analysis",
                    "optimal_preparation"):
            assert key in data, f"Missing key: {key}"


# ══════════════════════════════════════════════════════════════════════════
# /api/recipes/dosha
# ══════════════════════════════════════════════════════════════════════════

class TestDoshaRecipes:

    def test_invalid_dosha_returns_400(self, client):
        r = client.post("/api/recipes/dosha", json={"dosha": "invalid"})
        assert r.status_code == 400

    def test_missing_dosha_returns_400(self, client):
        r = client.post("/api/recipes/dosha", json={})
        assert r.status_code == 400

    @pytest.mark.parametrize("dosha", ["vata", "pitta", "kapha", "tridoshic"])
    def test_all_valid_doshas_accepted(self, client, dosha):
        mock = json.dumps({
            "dosha": dosha,
            "dosha_description": f"{dosha} description",
            "foods_to_favor": ["warm food"],
            "foods_to_avoid": ["cold food"],
            "recipes": []
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/dosha", json={"dosha": dosha})
        assert r.status_code == 200
        assert r.get_json()["dosha"] == dosha

    def test_vata_returns_recipes(self, client):
        mock = json.dumps({
            "dosha": "vata",
            "dosha_description": "Air and space — needs grounding",
            "foods_to_favor": ["ghee", "warm milk", "sweet potato"],
            "foods_to_avoid": ["raw salad", "cold drinks", "dry crackers"],
            "recipes": [
                {"name": "Golden Milk", "emoji": "🌿",
                 "meal_type": "Snack",
                 "dosha_effect": "Balancing",
                 "key_ayurvedic_ingredients": ["turmeric", "ghee", "milk"],
                 "description": "Warming vata-balancing drink",
                 "ingredients": ["250ml milk", "1 tsp turmeric", "1 tsp ghee"],
                 "steps": ["Heat milk", "Add turmeric and ghee"],
                 "time": "5 min",
                 "best_time_to_eat": "Evening",
                 "nutrition_per_serving": {"calories": 180, "protein": 8},
                 "ayurvedic_benefit": "Grounds vata, promotes sleep"}
            ]
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/dosha", json={"dosha": "vata"})
        data = r.get_json()
        assert len(data["recipes"]) == 1
        assert data["recipes"][0]["dosha_effect"] == "Balancing"

    def test_foods_to_favor_and_avoid_present(self, client):
        mock = json.dumps({
            "dosha": "pitta",
            "dosha_description": "Fire and water",
            "foods_to_favor": ["cucumber", "coconut", "mint"],
            "foods_to_avoid": ["chili", "garlic", "onion"],
            "recipes": []
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/dosha", json={"dosha": "pitta"})
        data = r.get_json()
        assert len(data["foods_to_favor"]) > 0
        assert len(data["foods_to_avoid"]) > 0

    def test_season_parameter_accepted(self, client):
        mock = json.dumps({
            "dosha": "kapha", "dosha_description": "Earth and water",
            "foods_to_favor": ["ginger", "pepper"], "foods_to_avoid": ["dairy"],
            "recipes": []
        })
        with _patch_gen(mock):
            r = client.post("/api/recipes/dosha",
                            json={"dosha": "kapha", "season": "winter"})
        assert r.status_code == 200


# ══════════════════════════════════════════════════════════════════════════
# New AI service functions (unit tests)
# ══════════════════════════════════════════════════════════════════════════

class TestNewAIFunctions:

    def test_translate_ingredient_returns_dict(self):
        mock = json.dumps({
            "english_name": "rice", "detected_language": "Hindi",
            "original_script": "चावल", "alternate_names": ["white rice"],
            "local_names": {}, "category": "grain", "confidence": "high"
        })
        with patch("ai_service._generate", return_value=mock):
            import ai_service
            result = ai_service.translate_ingredient("चावल")
        assert result["english_name"] == "rice"
        assert result["detected_language"] == "Hindi"

    def test_translate_ingredient_fallback_on_bad_json(self):
        with patch("ai_service._generate", return_value="not json at all"):
            import ai_service
            result = ai_service.translate_ingredient("unknown_word")
        assert result["english_name"] == "unknown_word"
        assert result["confidence"] == "low"

    def test_generate_from_ingredients_returns_dict(self):
        mock = json.dumps({"total_combinations": 2, "recipes": [
            {"name": "Dal Rice", "emoji": "🍲", "cuisine": "Indian",
             "method": "Boil", "time": "30 min", "difficulty": "Easy",
             "ingredients_used": ["rice", "lentils"], "missing_ingredients": [],
             "description": "Simple dal", "key_steps": ["Cook"],
             "nutrition_highlight": "Protein-rich", "calories_estimate": 400}
        ]})
        with patch("ai_service._generate", return_value=mock):
            import ai_service
            result = ai_service.generate_from_ingredients(["rice", "lentils"])
        assert result["total_combinations"] == 2
        assert len(result["recipes"]) == 1

    def test_generate_from_ingredients_fallback(self):
        with patch("ai_service._generate", return_value="bad response"):
            import ai_service
            result = ai_service.generate_from_ingredients(["egg"])
        assert result["total_combinations"] == 0
        assert result["recipes"] == []

    def test_generate_recipe_variations_returns_dict(self):
        mock = json.dumps({
            "original": "Omelette", "total_variations": 3,
            "variations": [
                {"name": "Baked", "type": "Method", "description": "Oven baked",
                 "key_changes": [], "ingredient_swaps": [],
                 "nutrition_impact": "Less fat", "time": "20 min",
                 "difficulty": "Easy", "best_for": "Diet"}
            ],
            "substitution_guide": {}
        })
        with patch("ai_service._generate", return_value=mock):
            import ai_service
            result = ai_service.generate_recipe_variations("Omelette")
        assert result["original"] == "Omelette"
        assert len(result["variations"]) == 1

    def test_generate_recipe_variations_fallback(self):
        with patch("ai_service._generate", return_value="not valid json"):
            import ai_service
            result = ai_service.generate_recipe_variations("Curry")
        assert result["original"] == "Curry"
        assert result["total_variations"] == 0

    def test_check_ayurvedic_compatibility_returns_dict(self):
        mock = json.dumps({
            "overall_compatibility": "Incompatible", "ayurvedic_score": 2.0,
            "nishidda_warnings": [{"combination": "milk + fish", "severity": "high",
                                   "reason": "Creates ama", "remedy": "Eat separately"}],
            "viruddhahara_flags": [], "shuddha_classification": [],
            "dosha_analysis": {}, "optimal_preparation": {},
            "ayurvedic_recipe_suggestion": ""
        })
        with patch("ai_service._generate", return_value=mock):
            import ai_service
            result = ai_service.check_ayurvedic_compatibility(["milk", "fish"])
        assert result["overall_compatibility"] == "Incompatible"
        assert len(result["nishidda_warnings"]) == 1

    def test_check_ayurvedic_compatibility_fallback(self):
        with patch("ai_service._generate", return_value="invalid"):
            import ai_service
            result = ai_service.check_ayurvedic_compatibility(["rice"])
        assert result["overall_compatibility"] == "Unknown"
        assert result["nishidda_warnings"] == []

    def test_get_dosha_recipes_returns_dict(self):
        mock = json.dumps({
            "dosha": "vata",
            "dosha_description": "Air and space element",
            "foods_to_favor": ["ghee", "warm milk"],
            "foods_to_avoid": ["cold food", "raw food"],
            "recipes": [{"name": "Warm Khichdi", "emoji": "🍲",
                         "meal_type": "Lunch", "dosha_effect": "Balancing",
                         "key_ayurvedic_ingredients": ["ghee", "cumin"],
                         "description": "Grounding meal",
                         "ingredients": ["100g rice", "50g dal"],
                         "steps": ["Cook together"],
                         "time": "30 min",
                         "best_time_to_eat": "Noon",
                         "nutrition_per_serving": {"calories": 350, "protein": 12},
                         "ayurvedic_benefit": "Grounds vata dosha"}]
        })
        with patch("ai_service._generate", return_value=mock):
            import ai_service
            result = ai_service.get_dosha_recipes("vata")
        assert result["dosha"] == "vata"
        assert len(result["recipes"]) == 1
        assert len(result["foods_to_favor"]) > 0

    def test_get_dosha_recipes_fallback(self):
        with patch("ai_service._generate", return_value="bad"):
            import ai_service
            result = ai_service.get_dosha_recipes("pitta")
        assert result["dosha"] == "pitta"
        assert result["recipes"] == []


# ══════════════════════════════════════════════════════════════════════════
# SQLite WAL mode
# ══════════════════════════════════════════════════════════════════════════

class TestSQLiteWAL:

    def test_wal_mode_can_be_enabled(self, app, _db_session):
        """WAL mode must be supported and settable on the SQLite database."""
        with app.app_context():
            from database import db
            db.session.execute(db.text("PRAGMA journal_mode=WAL"))
            db.session.commit()
            result = db.session.execute(db.text("PRAGMA journal_mode")).fetchone()
            assert result[0].lower() == "wal"

    def test_synchronous_can_be_set_to_normal(self, app, _db_session):
        """PRAGMA synchronous=NORMAL (1) must be supported."""
        with app.app_context():
            from database import db
            db.session.execute(db.text("PRAGMA synchronous=NORMAL"))
            result = db.session.execute(db.text("PRAGMA synchronous")).fetchone()
            assert result[0] == 1

    def test_cache_size_can_be_configured(self, app, _db_session):
        """Cache size pragma must be settable."""
        with app.app_context():
            from database import db
            db.session.execute(db.text("PRAGMA cache_size=10000"))
            result = db.session.execute(db.text("PRAGMA cache_size")).fetchone()
            # SQLite stores cache_size as negative (pages) when set via pragma
            assert result[0] != 0


# ══════════════════════════════════════════════════════════════════════════
# Multilingual chat — language parameter
# ══════════════════════════════════════════════════════════════════════════

class TestMultilingualChat:

    def test_chat_accepts_language_parameter(self, client):
        with patch("ai_service._chat", return_value="नमस्ते! मैं आपकी मदद कर सकता हूं।"):
            r = client.post("/api/chat", json={
                "message": "मुझे खाने की जानकारी दो",
                "category": "nutrition",
                "language": "Hindi"
            })
        assert r.status_code == 200
        assert "reply" in r.get_json()

    def test_chat_without_language_still_works(self, client):
        with patch("ai_service._chat", return_value="Sure! Here are some tips."):
            r = client.post("/api/chat", json={
                "message": "What should I eat?",
                "category": "general"
            })
        assert r.status_code == 200

    def test_chat_reply_in_target_language(self, client):
        expected = "வணக்கம்! நான் உங்களுக்கு உதவ முடியும்."
        with patch("ai_service._chat", return_value=expected):
            r = client.post("/api/chat", json={
                "message": "ஆரோக்கியமான உணவு என்ன?",
                "category": "nutrition",
                "language": "Tamil"
            })
        assert r.get_json()["reply"] == expected

    def test_chat_empty_language_auto_detects(self, client):
        with patch("ai_service._chat", return_value="Hola! Puedo ayudarte con nutrición."):
            r = client.post("/api/chat", json={
                "message": "¿Qué debo comer para perder peso?",
                "category": "nutrition",
                "language": ""
            })
        assert r.status_code == 200

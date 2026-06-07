"""
Comprehensive nutrition database with accurate USDA-based values.
All values per 100g unless otherwise noted.
"""

FOOD_DATABASE = {
    "chicken_breast": {
        "name": "Chicken Breast (cooked)",
        "aliases": ["chicken breast", "grilled chicken", "baked chicken", "chicken"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 165, "protein": 31.0, "carbs": 0.0, "sugar": 0.0, "fiber": 0.0,
        "fat": 3.6, "saturated_fat": 1.0, "monounsaturated_fat": 1.2, "polyunsaturated_fat": 0.8,
        "omega3": 0.05, "omega6": 0.70, "cholesterol": 85,
        "vitamins": {"a": 9, "b1": 0.07, "b2": 0.11, "b3": 12.5, "b5": 1.1, "b6": 0.80, "b9": 4, "b12": 0.30, "c": 0, "d": 0.1, "e": 0.3, "k": 0},
        "minerals": {"calcium": 10, "iron": 0.9, "magnesium": 25, "phosphorus": 220, "potassium": 256, "sodium": 63, "zinc": 1.0, "selenium": 24},
        "amino_acids": {"tryptophan": 0.33, "threonine": 1.40, "isoleucine": 1.60, "leucine": 2.60, "lysine": 2.80, "methionine": 0.90, "phenylalanine": 1.30, "valine": 1.70, "histidine": 1.00}
    },
    "salmon": {
        "name": "Salmon (cooked)",
        "aliases": ["salmon", "atlantic salmon", "baked salmon", "grilled salmon"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 206, "protein": 28.8, "carbs": 0.0, "sugar": 0.0, "fiber": 0.0,
        "fat": 10.5, "saturated_fat": 2.1, "monounsaturated_fat": 3.5, "polyunsaturated_fat": 3.7,
        "omega3": 2.26, "omega6": 0.98, "cholesterol": 85,
        "vitamins": {"a": 50, "b1": 0.25, "b2": 0.47, "b3": 9.0, "b5": 1.66, "b6": 0.87, "b9": 30, "b12": 4.15, "c": 0, "d": 14.5, "e": 1.1, "k": 0},
        "minerals": {"calcium": 13, "iron": 0.9, "magnesium": 37, "phosphorus": 371, "potassium": 628, "sodium": 59, "zinc": 0.8, "selenium": 46},
        "amino_acids": {"tryptophan": 0.33, "threonine": 1.28, "isoleucine": 1.33, "leucine": 2.35, "lysine": 2.65, "methionine": 0.87, "phenylalanine": 1.16, "valine": 1.51, "histidine": 0.88}
    },
    "tuna_canned": {
        "name": "Tuna (canned in water)",
        "aliases": ["tuna", "canned tuna", "tuna fish"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 116, "protein": 25.5, "carbs": 0.0, "sugar": 0.0, "fiber": 0.0,
        "fat": 1.0, "saturated_fat": 0.25, "monounsaturated_fat": 0.21, "polyunsaturated_fat": 0.35,
        "omega3": 0.28, "omega6": 0.03, "cholesterol": 42,
        "vitamins": {"a": 17, "b1": 0.03, "b2": 0.10, "b3": 11.7, "b5": 0.22, "b6": 0.46, "b9": 6, "b12": 2.15, "c": 0, "d": 1.7, "e": 0.5, "k": 0},
        "minerals": {"calcium": 11, "iron": 1.3, "magnesium": 35, "phosphorus": 267, "potassium": 237, "sodium": 396, "zinc": 0.9, "selenium": 80},
        "amino_acids": {"tryptophan": 0.29, "threonine": 1.13, "isoleucine": 1.18, "leucine": 2.08, "lysine": 2.36, "methionine": 0.77, "phenylalanine": 1.03, "valine": 1.34, "histidine": 0.78}
    },
    "eggs": {
        "name": "Eggs (whole, large)",
        "aliases": ["egg", "eggs", "whole egg", "boiled egg", "fried egg", "scrambled eggs"],
        "serving_size": 50, "serving_unit": "g (1 large egg)",
        "calories": 155, "protein": 12.6, "carbs": 1.1, "sugar": 0.6, "fiber": 0.0,
        "fat": 10.6, "saturated_fat": 3.3, "monounsaturated_fat": 4.1, "polyunsaturated_fat": 1.4,
        "omega3": 0.09, "omega6": 1.23, "cholesterol": 373,
        "vitamins": {"a": 149, "b1": 0.04, "b2": 0.46, "b3": 0.1, "b5": 1.53, "b6": 0.17, "b9": 47, "b12": 1.11, "c": 0, "d": 2.0, "e": 1.1, "k": 0.3},
        "minerals": {"calcium": 53, "iron": 1.8, "magnesium": 12, "phosphorus": 191, "potassium": 134, "sodium": 124, "zinc": 1.1, "selenium": 30},
        "amino_acids": {"tryptophan": 0.17, "threonine": 0.60, "isoleucine": 0.67, "leucine": 1.08, "lysine": 0.91, "methionine": 0.39, "phenylalanine": 0.68, "valine": 0.86, "histidine": 0.30}
    },
    "greek_yogurt": {
        "name": "Greek Yogurt (plain, full fat)",
        "aliases": ["greek yogurt", "greek yoghurt", "yogurt", "yoghurt"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 97, "protein": 9.0, "carbs": 3.6, "sugar": 3.2, "fiber": 0.0,
        "fat": 5.0, "saturated_fat": 3.3, "monounsaturated_fat": 1.3, "polyunsaturated_fat": 0.16,
        "omega3": 0.04, "omega6": 0.11, "cholesterol": 17,
        "vitamins": {"a": 46, "b1": 0.02, "b2": 0.27, "b3": 0.2, "b5": 0.49, "b6": 0.06, "b9": 7, "b12": 0.75, "c": 0, "d": 0, "e": 0.1, "k": 0},
        "minerals": {"calcium": 115, "iron": 0.1, "magnesium": 11, "phosphorus": 135, "potassium": 141, "sodium": 36, "zinc": 0.6, "selenium": 9},
        "amino_acids": {"tryptophan": 0.10, "threonine": 0.38, "isoleucine": 0.44, "leucine": 0.83, "lysine": 0.71, "methionine": 0.23, "phenylalanine": 0.43, "valine": 0.57, "histidine": 0.26}
    },
    "milk_whole": {
        "name": "Whole Milk",
        "aliases": ["milk", "whole milk", "cow milk", "full fat milk"],
        "serving_size": 240, "serving_unit": "ml (1 cup)",
        "calories": 61, "protein": 3.2, "carbs": 4.8, "sugar": 5.1, "fiber": 0.0,
        "fat": 3.3, "saturated_fat": 1.9, "monounsaturated_fat": 0.8, "polyunsaturated_fat": 0.12,
        "omega3": 0.08, "omega6": 0.07, "cholesterol": 10,
        "vitamins": {"a": 46, "b1": 0.04, "b2": 0.17, "b3": 0.1, "b5": 0.37, "b6": 0.04, "b9": 5, "b12": 0.44, "c": 0, "d": 1.3, "e": 0.1, "k": 0.3},
        "minerals": {"calcium": 113, "iron": 0.0, "magnesium": 10, "phosphorus": 84, "potassium": 143, "sodium": 40, "zinc": 0.4, "selenium": 3.7},
        "amino_acids": {"tryptophan": 0.05, "threonine": 0.13, "isoleucine": 0.16, "leucine": 0.27, "lysine": 0.22, "methionine": 0.08, "phenylalanine": 0.16, "valine": 0.19, "histidine": 0.08}
    },
    "cheddar_cheese": {
        "name": "Cheddar Cheese",
        "aliases": ["cheddar", "cheddar cheese", "cheese"],
        "serving_size": 28, "serving_unit": "g (1 oz)",
        "calories": 403, "protein": 24.9, "carbs": 1.3, "sugar": 0.5, "fiber": 0.0,
        "fat": 33.1, "saturated_fat": 21.1, "monounsaturated_fat": 9.4, "polyunsaturated_fat": 0.9,
        "omega3": 0.36, "omega6": 0.52, "cholesterol": 105,
        "vitamins": {"a": 330, "b1": 0.03, "b2": 0.37, "b3": 0.08, "b5": 0.41, "b6": 0.07, "b9": 18, "b12": 1.10, "c": 0, "d": 0.3, "e": 0.3, "k": 2.8},
        "minerals": {"calcium": 721, "iron": 0.7, "magnesium": 28, "phosphorus": 512, "potassium": 98, "sodium": 621, "zinc": 3.1, "selenium": 14},
        "amino_acids": {"tryptophan": 0.32, "threonine": 0.88, "isoleucine": 1.28, "leucine": 2.44, "lysine": 1.85, "methionine": 0.65, "phenylalanine": 1.35, "valine": 1.67, "histidine": 0.84}
    },
    "beef_lean": {
        "name": "Ground Beef (lean, cooked)",
        "aliases": ["beef", "ground beef", "hamburger meat", "lean beef", "minced beef"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 218, "protein": 26.1, "carbs": 0.0, "sugar": 0.0, "fiber": 0.0,
        "fat": 11.8, "saturated_fat": 4.6, "monounsaturated_fat": 5.1, "polyunsaturated_fat": 0.4,
        "omega3": 0.08, "omega6": 0.29, "cholesterol": 88,
        "vitamins": {"a": 0, "b1": 0.05, "b2": 0.22, "b3": 5.8, "b5": 0.62, "b6": 0.45, "b9": 9, "b12": 2.64, "c": 0, "d": 0.1, "e": 0.5, "k": 1.7},
        "minerals": {"calcium": 18, "iron": 2.7, "magnesium": 22, "phosphorus": 199, "potassium": 318, "sodium": 77, "zinc": 5.7, "selenium": 19},
        "amino_acids": {"tryptophan": 0.27, "threonine": 1.08, "isoleucine": 1.16, "leucine": 2.04, "lysine": 2.14, "methionine": 0.67, "phenylalanine": 1.03, "valine": 1.31, "histidine": 0.82}
    },
    "tofu_firm": {
        "name": "Tofu (firm)",
        "aliases": ["tofu", "firm tofu", "bean curd", "soy tofu"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 76, "protein": 8.1, "carbs": 1.9, "sugar": 0.7, "fiber": 0.3,
        "fat": 4.2, "saturated_fat": 0.6, "monounsaturated_fat": 0.9, "polyunsaturated_fat": 2.4,
        "omega3": 0.49, "omega6": 1.77, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.10, "b2": 0.06, "b3": 0.2, "b5": 0.07, "b6": 0.05, "b9": 15, "b12": 0.0, "c": 0.1, "d": 0, "e": 0.1, "k": 2.0},
        "minerals": {"calcium": 350, "iron": 2.7, "magnesium": 37, "phosphorus": 97, "potassium": 150, "sodium": 7, "zinc": 0.8, "selenium": 8.9},
        "amino_acids": {"tryptophan": 0.12, "threonine": 0.35, "isoleucine": 0.40, "leucine": 0.62, "lysine": 0.52, "methionine": 0.10, "phenylalanine": 0.42, "valine": 0.44, "histidine": 0.22}
    },
    "lentils": {
        "name": "Lentils (cooked)",
        "aliases": ["lentils", "cooked lentils", "red lentils", "green lentils", "dal"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 116, "protein": 9.0, "carbs": 20.1, "sugar": 1.8, "fiber": 7.9,
        "fat": 0.4, "saturated_fat": 0.05, "monounsaturated_fat": 0.07, "polyunsaturated_fat": 0.18,
        "omega3": 0.07, "omega6": 0.11, "cholesterol": 0,
        "vitamins": {"a": 1, "b1": 0.17, "b2": 0.07, "b3": 1.1, "b5": 0.64, "b6": 0.18, "b9": 181, "b12": 0.0, "c": 1.5, "d": 0, "e": 0.1, "k": 1.7},
        "minerals": {"calcium": 19, "iron": 3.3, "magnesium": 36, "phosphorus": 180, "potassium": 369, "sodium": 2, "zinc": 1.3, "selenium": 2.8},
        "amino_acids": {"tryptophan": 0.10, "threonine": 0.39, "isoleucine": 0.43, "leucine": 0.70, "lysine": 0.62, "methionine": 0.08, "phenylalanine": 0.50, "valine": 0.49, "histidine": 0.27}
    },
    "chickpeas": {
        "name": "Chickpeas (cooked)",
        "aliases": ["chickpeas", "garbanzo beans", "chick peas", "hummus base"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 164, "protein": 8.9, "carbs": 27.4, "sugar": 4.8, "fiber": 7.6,
        "fat": 2.6, "saturated_fat": 0.27, "monounsaturated_fat": 0.58, "polyunsaturated_fat": 1.16,
        "omega3": 0.07, "omega6": 1.08, "cholesterol": 0,
        "vitamins": {"a": 1, "b1": 0.12, "b2": 0.06, "b3": 0.5, "b5": 0.29, "b6": 0.14, "b9": 172, "b12": 0.0, "c": 1.3, "d": 0, "e": 0.4, "k": 4.0},
        "minerals": {"calcium": 49, "iron": 2.9, "magnesium": 48, "phosphorus": 168, "potassium": 291, "sodium": 7, "zinc": 1.5, "selenium": 3.7},
        "amino_acids": {"tryptophan": 0.09, "threonine": 0.34, "isoleucine": 0.38, "leucine": 0.62, "lysine": 0.57, "methionine": 0.10, "phenylalanine": 0.46, "valine": 0.43, "histidine": 0.23}
    },
    "quinoa": {
        "name": "Quinoa (cooked)",
        "aliases": ["quinoa", "cooked quinoa"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 120, "protein": 4.4, "carbs": 21.3, "sugar": 0.9, "fiber": 2.8,
        "fat": 1.9, "saturated_fat": 0.23, "monounsaturated_fat": 0.53, "polyunsaturated_fat": 1.0,
        "omega3": 0.18, "omega6": 0.80, "cholesterol": 0,
        "vitamins": {"a": 1, "b1": 0.10, "b2": 0.11, "b3": 0.4, "b5": 0.22, "b6": 0.12, "b9": 42, "b12": 0.0, "c": 0, "d": 0, "e": 0.6, "k": 0},
        "minerals": {"calcium": 17, "iron": 1.5, "magnesium": 64, "phosphorus": 152, "potassium": 172, "sodium": 7, "zinc": 1.1, "selenium": 2.8},
        "amino_acids": {"tryptophan": 0.05, "threonine": 0.17, "isoleucine": 0.18, "leucine": 0.30, "lysine": 0.24, "methionine": 0.06, "phenylalanine": 0.23, "valine": 0.21, "histidine": 0.13}
    },
    "brown_rice": {
        "name": "Brown Rice (cooked)",
        "aliases": ["brown rice", "cooked brown rice", "whole grain rice"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 122, "protein": 2.7, "carbs": 25.6, "sugar": 0.3, "fiber": 1.6,
        "fat": 1.0, "saturated_fat": 0.20, "monounsaturated_fat": 0.37, "polyunsaturated_fat": 0.35,
        "omega3": 0.02, "omega6": 0.32, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.14, "b2": 0.03, "b3": 1.5, "b5": 0.39, "b6": 0.15, "b9": 4, "b12": 0.0, "c": 0, "d": 0, "e": 0.1, "k": 0},
        "minerals": {"calcium": 10, "iron": 0.6, "magnesium": 44, "phosphorus": 83, "potassium": 79, "sodium": 2, "zinc": 0.6, "selenium": 9.8},
        "amino_acids": {"tryptophan": 0.04, "threonine": 0.09, "isoleucine": 0.11, "leucine": 0.21, "lysine": 0.10, "methionine": 0.06, "phenylalanine": 0.14, "valine": 0.15, "histidine": 0.07}
    },
    "oats": {
        "name": "Oats / Oatmeal (cooked)",
        "aliases": ["oats", "oatmeal", "porridge", "rolled oats", "overnight oats"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 68, "protein": 2.4, "carbs": 12.0, "sugar": 0.3, "fiber": 1.7,
        "fat": 1.4, "saturated_fat": 0.26, "monounsaturated_fat": 0.46, "polyunsaturated_fat": 0.52,
        "omega3": 0.04, "omega6": 0.47, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.08, "b2": 0.03, "b3": 0.2, "b5": 0.17, "b6": 0.03, "b9": 5, "b12": 0.0, "c": 0, "d": 0, "e": 0.1, "k": 0},
        "minerals": {"calcium": 8, "iron": 0.7, "magnesium": 19, "phosphorus": 62, "potassium": 61, "sodium": 49, "zinc": 0.5, "selenium": 8.3},
        "amino_acids": {"tryptophan": 0.04, "threonine": 0.08, "isoleucine": 0.10, "leucine": 0.19, "lysine": 0.09, "methionine": 0.05, "phenylalanine": 0.13, "valine": 0.13, "histidine": 0.06}
    },
    "sweet_potato": {
        "name": "Sweet Potato (baked)",
        "aliases": ["sweet potato", "baked sweet potato", "yam", "sweet potatoes"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 103, "protein": 2.3, "carbs": 23.6, "sugar": 7.4, "fiber": 3.8,
        "fat": 0.1, "saturated_fat": 0.02, "monounsaturated_fat": 0.0, "polyunsaturated_fat": 0.04,
        "omega3": 0.01, "omega6": 0.03, "cholesterol": 0,
        "vitamins": {"a": 961, "b1": 0.10, "b2": 0.08, "b3": 1.5, "b5": 0.95, "b6": 0.29, "b9": 6, "b12": 0.0, "c": 19.6, "d": 0, "e": 0.3, "k": 1.5},
        "minerals": {"calcium": 38, "iron": 0.8, "magnesium": 27, "phosphorus": 54, "potassium": 475, "sodium": 36, "zinc": 0.3, "selenium": 0.6},
        "amino_acids": {"tryptophan": 0.03, "threonine": 0.09, "isoleucine": 0.09, "leucine": 0.13, "lysine": 0.09, "methionine": 0.03, "phenylalanine": 0.10, "valine": 0.12, "histidine": 0.05}
    },
    "broccoli": {
        "name": "Broccoli (cooked)",
        "aliases": ["broccoli", "cooked broccoli", "steamed broccoli", "broccoli florets"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 35, "protein": 2.4, "carbs": 7.2, "sugar": 1.7, "fiber": 3.3,
        "fat": 0.4, "saturated_fat": 0.07, "monounsaturated_fat": 0.03, "polyunsaturated_fat": 0.19,
        "omega3": 0.13, "omega6": 0.06, "cholesterol": 0,
        "vitamins": {"a": 77, "b1": 0.06, "b2": 0.13, "b3": 0.8, "b5": 0.59, "b6": 0.20, "b9": 108, "b12": 0.0, "c": 64.9, "d": 0, "e": 1.5, "k": 141},
        "minerals": {"calcium": 63, "iron": 0.9, "magnesium": 21, "phosphorus": 67, "potassium": 293, "sodium": 41, "zinc": 0.5, "selenium": 2.5},
        "amino_acids": {"tryptophan": 0.03, "threonine": 0.09, "isoleucine": 0.08, "leucine": 0.13, "lysine": 0.13, "methionine": 0.04, "phenylalanine": 0.09, "valine": 0.12, "histidine": 0.05}
    },
    "spinach": {
        "name": "Spinach (raw)",
        "aliases": ["spinach", "raw spinach", "baby spinach", "spinach leaves"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 23, "protein": 2.9, "carbs": 3.6, "sugar": 0.4, "fiber": 2.2,
        "fat": 0.4, "saturated_fat": 0.06, "monounsaturated_fat": 0.01, "polyunsaturated_fat": 0.17,
        "omega3": 0.14, "omega6": 0.03, "cholesterol": 0,
        "vitamins": {"a": 469, "b1": 0.08, "b2": 0.19, "b3": 0.7, "b5": 0.07, "b6": 0.20, "b9": 194, "b12": 0.0, "c": 28.1, "d": 0, "e": 2.0, "k": 483},
        "minerals": {"calcium": 99, "iron": 2.7, "magnesium": 79, "phosphorus": 49, "potassium": 558, "sodium": 79, "zinc": 0.5, "selenium": 1.0},
        "amino_acids": {"tryptophan": 0.04, "threonine": 0.12, "isoleucine": 0.15, "leucine": 0.22, "lysine": 0.17, "methionine": 0.05, "phenylalanine": 0.13, "valine": 0.16, "histidine": 0.06}
    },
    "avocado": {
        "name": "Avocado",
        "aliases": ["avocado", "avocados", "hass avocado"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 160, "protein": 2.0, "carbs": 8.5, "sugar": 0.7, "fiber": 6.7,
        "fat": 14.7, "saturated_fat": 2.1, "monounsaturated_fat": 9.8, "polyunsaturated_fat": 1.8,
        "omega3": 0.11, "omega6": 1.67, "cholesterol": 0,
        "vitamins": {"a": 7, "b1": 0.07, "b2": 0.13, "b3": 1.7, "b5": 1.39, "b6": 0.26, "b9": 81, "b12": 0.0, "c": 10.0, "d": 0, "e": 2.1, "k": 21},
        "minerals": {"calcium": 12, "iron": 0.6, "magnesium": 29, "phosphorus": 52, "potassium": 485, "sodium": 7, "zinc": 0.6, "selenium": 0.4},
        "amino_acids": {"tryptophan": 0.03, "threonine": 0.07, "isoleucine": 0.08, "leucine": 0.14, "lysine": 0.13, "methionine": 0.04, "phenylalanine": 0.10, "valine": 0.11, "histidine": 0.05}
    },
    "banana": {
        "name": "Banana",
        "aliases": ["banana", "bananas"],
        "serving_size": 118, "serving_unit": "g (1 medium)",
        "calories": 89, "protein": 1.1, "carbs": 22.8, "sugar": 12.2, "fiber": 2.6,
        "fat": 0.3, "saturated_fat": 0.11, "monounsaturated_fat": 0.03, "polyunsaturated_fat": 0.07,
        "omega3": 0.03, "omega6": 0.05, "cholesterol": 0,
        "vitamins": {"a": 3, "b1": 0.03, "b2": 0.07, "b3": 0.7, "b5": 0.33, "b6": 0.37, "b9": 20, "b12": 0.0, "c": 8.7, "d": 0, "e": 0.1, "k": 0.5},
        "minerals": {"calcium": 5, "iron": 0.3, "magnesium": 27, "phosphorus": 22, "potassium": 358, "sodium": 1, "zinc": 0.2, "selenium": 1.0},
        "amino_acids": {"tryptophan": 0.01, "threonine": 0.03, "isoleucine": 0.03, "leucine": 0.07, "lysine": 0.05, "methionine": 0.01, "phenylalanine": 0.05, "valine": 0.05, "histidine": 0.02}
    },
    "blueberries": {
        "name": "Blueberries",
        "aliases": ["blueberries", "blueberry"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 57, "protein": 0.7, "carbs": 14.5, "sugar": 9.9, "fiber": 2.4,
        "fat": 0.3, "saturated_fat": 0.03, "monounsaturated_fat": 0.05, "polyunsaturated_fat": 0.15,
        "omega3": 0.06, "omega6": 0.09, "cholesterol": 0,
        "vitamins": {"a": 3, "b1": 0.04, "b2": 0.04, "b3": 0.4, "b5": 0.12, "b6": 0.05, "b9": 6, "b12": 0.0, "c": 9.7, "d": 0, "e": 0.6, "k": 19},
        "minerals": {"calcium": 6, "iron": 0.3, "magnesium": 6, "phosphorus": 12, "potassium": 77, "sodium": 1, "zinc": 0.2, "selenium": 0.1},
        "amino_acids": {"tryptophan": 0.01, "threonine": 0.03, "isoleucine": 0.03, "leucine": 0.05, "lysine": 0.02, "methionine": 0.01, "phenylalanine": 0.03, "valine": 0.04, "histidine": 0.01}
    },
    "almonds": {
        "name": "Almonds",
        "aliases": ["almonds", "almond", "raw almonds", "roasted almonds"],
        "serving_size": 28, "serving_unit": "g (1 oz / ~23 nuts)",
        "calories": 579, "protein": 21.2, "carbs": 21.7, "sugar": 4.4, "fiber": 12.5,
        "fat": 49.9, "saturated_fat": 3.8, "monounsaturated_fat": 31.6, "polyunsaturated_fat": 12.3,
        "omega3": 0.004, "omega6": 12.1, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.21, "b2": 1.01, "b3": 3.6, "b5": 0.47, "b6": 0.14, "b9": 44, "b12": 0.0, "c": 0, "d": 0, "e": 25.6, "k": 0},
        "minerals": {"calcium": 264, "iron": 3.7, "magnesium": 270, "phosphorus": 481, "potassium": 733, "sodium": 1, "zinc": 3.1, "selenium": 4.1},
        "amino_acids": {"tryptophan": 0.21, "threonine": 0.60, "isoleucine": 0.75, "leucine": 1.47, "lysine": 0.58, "methionine": 0.15, "phenylalanine": 1.13, "valine": 0.85, "histidine": 0.54}
    },
    "walnuts": {
        "name": "Walnuts",
        "aliases": ["walnuts", "walnut", "english walnuts"],
        "serving_size": 28, "serving_unit": "g (1 oz)",
        "calories": 654, "protein": 15.2, "carbs": 13.7, "sugar": 2.6, "fiber": 6.7,
        "fat": 65.2, "saturated_fat": 6.1, "monounsaturated_fat": 8.9, "polyunsaturated_fat": 47.2,
        "omega3": 9.08, "omega6": 38.1, "cholesterol": 0,
        "vitamins": {"a": 1, "b1": 0.34, "b2": 0.15, "b3": 1.1, "b5": 0.57, "b6": 0.54, "b9": 98, "b12": 0.0, "c": 1.3, "d": 0, "e": 0.7, "k": 2.7},
        "minerals": {"calcium": 98, "iron": 2.9, "magnesium": 158, "phosphorus": 346, "potassium": 441, "sodium": 2, "zinc": 3.1, "selenium": 4.9},
        "amino_acids": {"tryptophan": 0.17, "threonine": 0.59, "isoleucine": 0.67, "leucine": 1.17, "lysine": 0.42, "methionine": 0.24, "phenylalanine": 0.71, "valine": 0.75, "histidine": 0.39}
    },
    "chia_seeds": {
        "name": "Chia Seeds",
        "aliases": ["chia seeds", "chia", "chia seed"],
        "serving_size": 28, "serving_unit": "g (2 tbsp)",
        "calories": 486, "protein": 16.5, "carbs": 42.1, "sugar": 0.0, "fiber": 34.4,
        "fat": 30.7, "saturated_fat": 3.3, "monounsaturated_fat": 2.3, "polyunsaturated_fat": 23.7,
        "omega3": 17.8, "omega6": 5.8, "cholesterol": 0,
        "vitamins": {"a": 54, "b1": 0.62, "b2": 0.17, "b3": 8.8, "b5": 0.94, "b6": 0.0, "b9": 49, "b12": 0.0, "c": 1.6, "d": 0, "e": 0.5, "k": 0},
        "minerals": {"calcium": 631, "iron": 7.7, "magnesium": 335, "phosphorus": 860, "potassium": 407, "sodium": 16, "zinc": 4.6, "selenium": 55.2},
        "amino_acids": {"tryptophan": 0.44, "threonine": 0.55, "isoleucine": 0.68, "leucine": 1.37, "lysine": 1.15, "methionine": 0.59, "phenylalanine": 1.01, "valine": 0.95, "histidine": 0.53}
    },
    "olive_oil": {
        "name": "Olive Oil",
        "aliases": ["olive oil", "extra virgin olive oil", "evoo"],
        "serving_size": 14, "serving_unit": "g (1 tbsp)",
        "calories": 884, "protein": 0.0, "carbs": 0.0, "sugar": 0.0, "fiber": 0.0,
        "fat": 100.0, "saturated_fat": 13.8, "monounsaturated_fat": 73.0, "polyunsaturated_fat": 10.5,
        "omega3": 0.76, "omega6": 9.76, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.0, "b2": 0.0, "b3": 0.0, "b5": 0.0, "b6": 0.0, "b9": 0, "b12": 0.0, "c": 0, "d": 0, "e": 14.4, "k": 60},
        "minerals": {"calcium": 1, "iron": 0.6, "magnesium": 0, "phosphorus": 0, "potassium": 1, "sodium": 2, "zinc": 0.0, "selenium": 0.5},
        "amino_acids": {}
    },
    "dark_chocolate": {
        "name": "Dark Chocolate (70-85%)",
        "aliases": ["dark chocolate", "bittersweet chocolate", "cocoa"],
        "serving_size": 28, "serving_unit": "g (1 oz)",
        "calories": 598, "protein": 7.8, "carbs": 45.9, "sugar": 23.9, "fiber": 10.9,
        "fat": 42.6, "saturated_fat": 24.5, "monounsaturated_fat": 13.0, "polyunsaturated_fat": 1.3,
        "omega3": 0.04, "omega6": 1.22, "cholesterol": 3,
        "vitamins": {"a": 2, "b1": 0.03, "b2": 0.07, "b3": 0.6, "b5": 0.19, "b6": 0.03, "b9": 4, "b12": 0.25, "c": 0, "d": 0, "e": 0.6, "k": 7.3},
        "minerals": {"calcium": 73, "iron": 11.9, "magnesium": 228, "phosphorus": 308, "potassium": 715, "sodium": 20, "zinc": 3.3, "selenium": 6.8},
        "amino_acids": {}
    },
    "orange": {
        "name": "Orange",
        "aliases": ["orange", "navel orange", "oranges"],
        "serving_size": 131, "serving_unit": "g (1 medium)",
        "calories": 47, "protein": 0.9, "carbs": 11.8, "sugar": 9.4, "fiber": 2.4,
        "fat": 0.1, "saturated_fat": 0.02, "monounsaturated_fat": 0.02, "polyunsaturated_fat": 0.02,
        "omega3": 0.01, "omega6": 0.02, "cholesterol": 0,
        "vitamins": {"a": 11, "b1": 0.09, "b2": 0.04, "b3": 0.3, "b5": 0.25, "b6": 0.06, "b9": 30, "b12": 0.0, "c": 53.2, "d": 0, "e": 0.2, "k": 0},
        "minerals": {"calcium": 40, "iron": 0.1, "magnesium": 10, "phosphorus": 14, "potassium": 181, "sodium": 0, "zinc": 0.1, "selenium": 0.5},
        "amino_acids": {}
    },
    "apple": {
        "name": "Apple",
        "aliases": ["apple", "apples", "green apple", "red apple"],
        "serving_size": 182, "serving_unit": "g (1 medium)",
        "calories": 52, "protein": 0.3, "carbs": 13.8, "sugar": 10.4, "fiber": 2.4,
        "fat": 0.2, "saturated_fat": 0.03, "monounsaturated_fat": 0.01, "polyunsaturated_fat": 0.05,
        "omega3": 0.01, "omega6": 0.04, "cholesterol": 0,
        "vitamins": {"a": 3, "b1": 0.02, "b2": 0.03, "b3": 0.1, "b5": 0.06, "b6": 0.04, "b9": 3, "b12": 0.0, "c": 4.6, "d": 0, "e": 0.2, "k": 2.2},
        "minerals": {"calcium": 6, "iron": 0.1, "magnesium": 5, "phosphorus": 11, "potassium": 107, "sodium": 1, "zinc": 0.0, "selenium": 0.0},
        "amino_acids": {}
    },
    "pasta": {
        "name": "Pasta (cooked, regular)",
        "aliases": ["pasta", "spaghetti", "penne", "noodles", "cooked pasta"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 157, "protein": 5.8, "carbs": 30.9, "sugar": 0.6, "fiber": 1.8,
        "fat": 0.9, "saturated_fat": 0.18, "monounsaturated_fat": 0.13, "polyunsaturated_fat": 0.34,
        "omega3": 0.03, "omega6": 0.31, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.02, "b2": 0.01, "b3": 1.1, "b5": 0.11, "b6": 0.05, "b9": 7, "b12": 0.0, "c": 0, "d": 0, "e": 0.1, "k": 0.1},
        "minerals": {"calcium": 7, "iron": 1.3, "magnesium": 18, "phosphorus": 58, "potassium": 44, "sodium": 1, "zinc": 0.5, "selenium": 26.4},
        "amino_acids": {"tryptophan": 0.07, "threonine": 0.19, "isoleucine": 0.24, "leucine": 0.43, "lysine": 0.18, "methionine": 0.09, "phenylalanine": 0.31, "valine": 0.27, "histidine": 0.14}
    },
    "tempeh": {
        "name": "Tempeh",
        "aliases": ["tempeh"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 193, "protein": 20.3, "carbs": 7.6, "sugar": 0.0, "fiber": 0.0,
        "fat": 10.8, "saturated_fat": 2.1, "monounsaturated_fat": 3.0, "polyunsaturated_fat": 5.2,
        "omega3": 0.26, "omega6": 4.95, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.08, "b2": 0.36, "b3": 2.6, "b5": 0.28, "b6": 0.22, "b9": 24, "b12": 0.0, "c": 0, "d": 0, "e": 0.0, "k": 0},
        "minerals": {"calcium": 111, "iron": 2.7, "magnesium": 81, "phosphorus": 266, "potassium": 412, "sodium": 9, "zinc": 1.1, "selenium": 0.1},
        "amino_acids": {"tryptophan": 0.27, "threonine": 0.81, "isoleucine": 0.93, "leucine": 1.49, "lysine": 1.16, "methionine": 0.27, "phenylalanine": 1.03, "valine": 1.01, "histidine": 0.51}
    },
    "pumpkin_seeds": {
        "name": "Pumpkin Seeds",
        "aliases": ["pumpkin seeds", "pepitas"],
        "serving_size": 28, "serving_unit": "g (1 oz)",
        "calories": 559, "protein": 30.2, "carbs": 10.7, "sugar": 1.4, "fiber": 6.0,
        "fat": 49.1, "saturated_fat": 8.7, "monounsaturated_fat": 16.4, "polyunsaturated_fat": 20.9,
        "omega3": 0.09, "omega6": 20.7, "cholesterol": 0,
        "vitamins": {"a": 16, "b1": 0.27, "b2": 0.32, "b3": 4.4, "b5": 0.75, "b6": 0.10, "b9": 57, "b12": 0.0, "c": 1.9, "d": 0, "e": 2.2, "k": 7.3},
        "minerals": {"calcium": 46, "iron": 8.8, "magnesium": 592, "phosphorus": 1233, "potassium": 809, "sodium": 7, "zinc": 7.8, "selenium": 9.4},
        "amino_acids": {"tryptophan": 0.58, "threonine": 0.78, "isoleucine": 1.28, "leucine": 2.42, "lysine": 1.39, "methionine": 0.60, "phenylalanine": 1.73, "valine": 1.56, "histidine": 0.79}
    },
    "black_beans": {
        "name": "Black Beans (cooked)",
        "aliases": ["black beans", "cooked black beans"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 132, "protein": 8.9, "carbs": 23.7, "sugar": 0.3, "fiber": 8.7,
        "fat": 0.5, "saturated_fat": 0.13, "monounsaturated_fat": 0.04, "polyunsaturated_fat": 0.21,
        "omega3": 0.18, "omega6": 0.02, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.24, "b2": 0.06, "b3": 0.5, "b5": 0.32, "b6": 0.07, "b9": 149, "b12": 0.0, "c": 0, "d": 0, "e": 0.3, "k": 5.6},
        "minerals": {"calcium": 27, "iron": 2.1, "magnesium": 70, "phosphorus": 140, "potassium": 355, "sodium": 1, "zinc": 1.0, "selenium": 1.2},
        "amino_acids": {"tryptophan": 0.11, "threonine": 0.37, "isoleucine": 0.38, "leucine": 0.69, "lysine": 0.60, "methionine": 0.14, "phenylalanine": 0.48, "valine": 0.47, "histidine": 0.25}
    },
    "white_rice": {
        "name": "White Rice (cooked)",
        "aliases": ["white rice", "rice", "cooked rice", "steamed rice"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 130, "protein": 2.7, "carbs": 28.2, "sugar": 0.0, "fiber": 0.4,
        "fat": 0.3, "saturated_fat": 0.08, "monounsaturated_fat": 0.07, "polyunsaturated_fat": 0.08,
        "omega3": 0.01, "omega6": 0.06, "cholesterol": 0,
        "vitamins": {"a": 0, "b1": 0.02, "b2": 0.01, "b3": 0.4, "b5": 0.19, "b6": 0.02, "b9": 3, "b12": 0.0, "c": 0, "d": 0, "e": 0.0, "k": 0},
        "minerals": {"calcium": 10, "iron": 0.2, "magnesium": 12, "phosphorus": 43, "potassium": 35, "sodium": 1, "zinc": 0.5, "selenium": 7.5},
        "amino_acids": {"tryptophan": 0.03, "threonine": 0.08, "isoleucine": 0.10, "leucine": 0.19, "lysine": 0.08, "methionine": 0.05, "phenylalanine": 0.13, "valine": 0.14, "histidine": 0.06}
    },
    "cottage_cheese": {
        "name": "Cottage Cheese (low fat)",
        "aliases": ["cottage cheese", "paneer"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 98, "protein": 11.1, "carbs": 3.4, "sugar": 2.7, "fiber": 0.0,
        "fat": 4.3, "saturated_fat": 1.7, "monounsaturated_fat": 1.2, "polyunsaturated_fat": 0.13,
        "omega3": 0.05, "omega6": 0.07, "cholesterol": 17,
        "vitamins": {"a": 37, "b1": 0.02, "b2": 0.16, "b3": 0.1, "b5": 0.22, "b6": 0.07, "b9": 12, "b12": 0.43, "c": 0, "d": 0.1, "e": 0.1, "k": 0},
        "minerals": {"calcium": 83, "iron": 0.1, "magnesium": 8, "phosphorus": 159, "potassium": 104, "sodium": 364, "zinc": 0.4, "selenium": 9.7},
        "amino_acids": {"tryptophan": 0.13, "threonine": 0.44, "isoleucine": 0.60, "leucine": 1.00, "lysine": 0.96, "methionine": 0.29, "phenylalanine": 0.56, "valine": 0.72, "histidine": 0.35}
    },
    "kale": {
        "name": "Kale (raw)",
        "aliases": ["kale", "raw kale", "curly kale"],
        "serving_size": 100, "serving_unit": "g",
        "calories": 49, "protein": 4.3, "carbs": 8.8, "sugar": 2.3, "fiber": 3.6,
        "fat": 0.9, "saturated_fat": 0.09, "monounsaturated_fat": 0.07, "polyunsaturated_fat": 0.44,
        "omega3": 0.18, "omega6": 0.26, "cholesterol": 0,
        "vitamins": {"a": 500, "b1": 0.11, "b2": 0.13, "b3": 1.0, "b5": 0.09, "b6": 0.27, "b9": 141, "b12": 0.0, "c": 120, "d": 0, "e": 1.5, "k": 704},
        "minerals": {"calcium": 150, "iron": 1.5, "magnesium": 47, "phosphorus": 92, "potassium": 491, "sodium": 38, "zinc": 0.6, "selenium": 0.9},
        "amino_acids": {"tryptophan": 0.06, "threonine": 0.18, "isoleucine": 0.18, "leucine": 0.28, "lysine": 0.28, "methionine": 0.07, "phenylalanine": 0.18, "valine": 0.22, "histidine": 0.09}
    }
}


RDA = {
    "calories": 2000,
    "protein": 50,
    "carbs": 275,
    "fiber": 28,
    "fat": 78,
    "saturated_fat": 20,
    "omega3": 1.6,
    "omega6": 17.0,
    "vitamins": {
        "a": 900,      # mcg RAE
        "b1": 1.2,     # mg
        "b2": 1.3,     # mg
        "b3": 16.0,    # mg
        "b5": 5.0,     # mg
        "b6": 1.7,     # mg
        "b9": 400,     # mcg
        "b12": 2.4,    # mcg
        "c": 90,       # mg
        "d": 15,       # mcg
        "e": 15,       # mg
        "k": 120       # mcg
    },
    "minerals": {
        "calcium": 1000,     # mg
        "iron": 8,           # mg
        "magnesium": 420,    # mg
        "phosphorus": 700,   # mg
        "potassium": 3400,   # mg
        "sodium": 2300,      # mg
        "zinc": 11,          # mg
        "selenium": 55       # mcg
    },
    "amino_acids": {
        "tryptophan": 0.28,
        "threonine": 1.05,
        "isoleucine": 1.40,
        "leucine": 2.73,
        "lysine": 2.10,
        "methionine": 0.73,
        "phenylalanine": 1.89,
        "valine": 1.82,
        "histidine": 0.70
    }
}

VITAMIN_NAMES = {
    "a": "Vitamin A", "b1": "Vitamin B1 (Thiamine)", "b2": "Vitamin B2 (Riboflavin)",
    "b3": "Vitamin B3 (Niacin)", "b5": "Vitamin B5 (Pantothenic Acid)", "b6": "Vitamin B6",
    "b9": "Vitamin B9 (Folate)", "b12": "Vitamin B12", "c": "Vitamin C",
    "d": "Vitamin D", "e": "Vitamin E", "k": "Vitamin K"
}

VITAMIN_UNITS = {
    "a": "mcg", "b1": "mg", "b2": "mg", "b3": "mg", "b5": "mg", "b6": "mg",
    "b9": "mcg", "b12": "mcg", "c": "mg", "d": "mcg", "e": "mg", "k": "mcg"
}

MINERAL_NAMES = {
    "calcium": "Calcium", "iron": "Iron", "magnesium": "Magnesium",
    "phosphorus": "Phosphorus", "potassium": "Potassium", "sodium": "Sodium",
    "zinc": "Zinc", "selenium": "Selenium"
}

AMINO_ACID_NAMES = {
    "tryptophan": "Tryptophan", "threonine": "Threonine", "isoleucine": "Isoleucine",
    "leucine": "Leucine", "lysine": "Lysine", "methionine": "Methionine",
    "phenylalanine": "Phenylalanine", "valine": "Valine", "histidine": "Histidine"
}

AMINO_ACID_ROLES = {
    "tryptophan": "Precursor to serotonin & melatonin — mood, sleep, happiness",
    "threonine": "Immune function, collagen & elastin synthesis, gut health",
    "isoleucine": "Muscle repair, energy regulation, immune response",
    "leucine": "Primary muscle protein synthesis trigger, wound healing",
    "lysine": "Collagen production, calcium absorption, immune function",
    "methionine": "Antioxidant (glutathione precursor), liver health, metabolism",
    "phenylalanine": "Neurotransmitter precursor (dopamine, norepinephrine, epinephrine)",
    "valine": "Muscle growth, energy production, nervous system support",
    "histidine": "Immune function, nerve function, antioxidant (carnosine precursor)"
}


def search_food_local(query: str) -> list:
    """Search local food database by name/alias."""
    query_lower = query.lower().strip()
    results = []
    for key, food in FOOD_DATABASE.items():
        if (query_lower in food["name"].lower() or
                any(query_lower in alias.lower() for alias in food.get("aliases", []))):
            results.append({"key": key, **food})
    return results[:10]


def calculate_nutrition_totals(food_logs: list) -> dict:
    """Sum up nutrition from multiple food log entries."""
    totals = {
        "calories": 0, "protein": 0, "carbs": 0, "sugar": 0, "fiber": 0,
        "fat": 0, "saturated_fat": 0, "monounsaturated_fat": 0, "polyunsaturated_fat": 0,
        "omega3": 0, "omega6": 0,
        "vitamins": {k: 0 for k in VITAMIN_NAMES},
        "minerals": {k: 0 for k in MINERAL_NAMES},
        "amino_acids": {k: 0 for k in AMINO_ACID_NAMES}
    }
    for log in food_logs:
        ratio = log.get("quantity", 100) / 100.0
        n = log.get("nutrition", {})
        for macro in ["calories", "protein", "carbs", "sugar", "fiber", "fat",
                      "saturated_fat", "monounsaturated_fat", "polyunsaturated_fat",
                      "omega3", "omega6"]:
            totals[macro] += n.get(macro, 0) * ratio
        for cat in ["vitamins", "minerals", "amino_acids"]:
            for key in totals[cat]:
                totals[cat][key] += n.get(cat, {}).get(key, 0) * ratio
    return totals


def calculate_deficiencies(totals: dict, user_rda: dict = None) -> dict:
    """Calculate nutrient deficiencies as percentages."""
    rda = user_rda or RDA
    deficiencies = {}
    for macro in ["calories", "protein", "carbs", "fiber", "fat", "omega3", "omega6"]:
        if macro in rda:
            pct = min((totals.get(macro, 0) / rda[macro]) * 100, 200)
            deficiencies[macro] = round(pct, 1)
    for cat in ["vitamins", "minerals", "amino_acids"]:
        deficiencies[cat] = {}
        for key, target in rda.get(cat, {}).items():
            val = totals.get(cat, {}).get(key, 0)
            pct = min((val / target) * 100, 200) if target > 0 else 0
            deficiencies[cat][key] = round(pct, 1)
    return deficiencies


def calculate_personal_rda(weight_kg: float, height_cm: float, age: int,
                            gender: str, activity_level: str, goal: str) -> dict:
    """Calculate personalized RDA based on user profile."""
    if gender == "male":
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    activity_multipliers = {
        "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
        "active": 1.725, "very_active": 1.9
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)
    if goal == "lose":
        calorie_target = tdee - 500
    elif goal == "gain":
        calorie_target = tdee + 300
    else:
        calorie_target = tdee
    protein_target = weight_kg * 1.6 if goal == "gain" else weight_kg * 1.2
    # Scale macros proportionally from the personalised calorie target.
    # Ratios: carbs 55% of kcal (/4), fat 35% (/9), fiber 14g per 1000 kcal.
    carb_target = round(calorie_target * 0.55 / 4)
    fat_target = round(calorie_target * 0.35 / 9)
    fiber_target = round(calorie_target * 14 / 1000)
    personal_rda = RDA.copy()
    personal_rda["calories"] = round(calorie_target)
    personal_rda["protein"] = round(protein_target)
    personal_rda["carbs"] = carb_target
    personal_rda["fat"] = fat_target
    personal_rda["fiber"] = fiber_target
    personal_rda["amino_acids"] = {
        k: round(v * (weight_kg / 70), 2) for k, v in RDA["amino_acids"].items()
    }
    if gender == "female":
        personal_rda["minerals"] = {**RDA["minerals"], "iron": 18}
    return personal_rda

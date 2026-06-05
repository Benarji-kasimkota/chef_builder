# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app (requires GEMINI_API_KEY in .env)
python app.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_api.py -v

# Run a single test class or function
pytest tests/test_api.py::TestFoodLog::test_log_food_returns_id -v
```

## Architecture

**Single-file Flask app** — all routes live in [app.py](app.py). No blueprints.

**AI layer** — [ai_service.py](ai_service.py) wraps Google Gemini (`google-genai` SDK). All AI calls use `_generate()` (single-turn) or `_chat()` (multi-turn). The model is set via `GEMINI_MODEL` env var, defaulting to `gemini-flash-lite-latest`. The client is a module-level singleton.

**Database** — SQLAlchemy + SQLite (`instance/chefbuilder.db`). WAL mode is enabled at connection time in [app.py](app.py). Models are in [models.py](models.py): `UserProfile` (singleton row), `FoodLog`, `MindfulnessLog`, `WeightLog`, `WaterLog`, `ChatMessage`.

**Nutrition engine** — [nutrition_data.py](nutrition_data.py) contains the built-in `FOOD_DATABASE`, `RDA` values, and pure functions: `search_food_local`, `calculate_nutrition_totals`, `calculate_deficiencies`, `calculate_personal_rda`. `FoodLog.nutrition` is stored as JSON in `nutrition_json` column (pre-scaled to quantity at log time).

**External food data** — USDA FoodData Central API (`USDA_API_KEY`, defaults to `DEMO_KEY`) and Open Food Facts barcode API (no key needed).

**Frontend** — Jinja2 templates with vanilla JS + Chart.js + Lucide icons. Dark glassmorphism design system in [static/css/style.css](static/css/style.css). No build step.

## Key Design Decisions

- `FoodLog.nutrition_json` stores already-scaled macros (per `quantity_g`). When calculating totals, always pass `quantity=100` so the ratio is 1:1 (see `logs_to_nutrition_list` in app.py).
- `UserProfile` is always a single row — `get_profile()` returns `UserProfile.query.first()`.
- Custom macro targets (`custom_calories`, etc.) override auto-calculated RDA when non-zero — see `get_effective_rda()`.
- AI responses that return JSON use `re.search(r'\{.*\}', text, re.DOTALL)` to extract the JSON block — always wrap AI JSON calls in this pattern.

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google Gemini AI |
| `GEMINI_MODEL` | No | `gemini-flash-lite-latest` | Model override |
| `USDA_API_KEY` | No | `DEMO_KEY` | USDA food data (rate-limited) |
| `SECRET_KEY` | No | hardcoded dev key | Flask session secret |
| `DATABASE_URL` | No | `sqlite:///chefbuilder.db` | SQLAlchemy URI |

## Testing

Tests in [tests/](tests/) use pytest with Flask test client. The `conftest.py` sets `DATABASE_URL` to a temp SQLite file before imports. All AI calls must be mocked — patch `ai_service._generate` or `ai_service._chat` directly. A pre-configured `UserProfile` (onboarding complete) is created once per session by `_db_session` fixture.

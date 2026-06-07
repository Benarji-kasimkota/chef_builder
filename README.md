# Chef Builder

A personal nutrition and wellness tracker powered by Google Gemini AI. Log meals, track macros against your personalized RDA, get AI coaching, and analyze meal photos — all in a dark glassmorphism web UI.

## Features

- **Food logging** — search a built-in database, USDA FoodData Central, or Open Food Facts (barcode)
- **Personalized RDA** — calorie, macro, vitamin, and mineral targets calculated from your profile (weight, height, age, activity level, goal)
- **AI meal analysis** — upload a photo and Gemini Vision estimates the nutrition
- **AI Coach** — multi-turn chat for nutrition advice and recipe help
- **Mindfulness & water logging**
- **Weight tracking with chart**

## Setup

### Prerequisites

- Python 3.11+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- (Optional) A [USDA FoodData Central API key](https://fdc.nal.usda.gov/api-guide.html) — defaults to the rate-limited `DEMO_KEY`

### Local development

```bash
# 1. Clone and create a virtualenv
python -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

# 4. Run
python app.py
```

The app starts at `http://localhost:5000`.

### Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google Gemini AI |
| `GEMINI_MODEL` | No | `gemini-flash-lite-latest` | Model override |
| `USDA_API_KEY` | No | `DEMO_KEY` | USDA food data (rate-limited without key) |
| `SECRET_KEY` | No | hardcoded dev key | Flask session secret — set a real one in prod |
| `DATABASE_URL` | No | `sqlite:///chefbuilder.db` | SQLAlchemy URI |

### Deploy to Render

Push to GitHub and connect the repo in Render. The included `render.yaml` configures the service automatically — just add `GEMINI_API_KEY` as a secret env var in the Render dashboard.

## Testing

```bash
pytest          # run all tests
pytest tests/test_api.py -v   # single file, verbose
```

## Architecture

Single-file Flask app (`app.py`). AI calls go through `ai_service.py` (Google Gemini). Database is SQLAlchemy + SQLite. No frontend build step — vanilla JS, Chart.js, Lucide icons. See [CLAUDE.md](CLAUDE.md) for developer details.

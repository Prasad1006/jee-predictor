# Architecture — AI JoSAA Counselling Copilot

## System overview

```
┌──────────────┐     ┌─────────────────────────────────────────┐
│  Next.js     │     │  Django REST API (backend/django-app)    │
│  (Step 7)    │────▶│  /api/v1/predict/                        │
└──────────────┘     │  /api/v1/preferences/generate/           │
                     │  /api/v1/colleges/...                    │
                     └───────────┬─────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌────────────────┐ ┌───────────────┐ ┌─────────────────┐
     │ recommendation │ │  PostgreSQL   │ │  RAG + Gemini   │
     │ _engine        │ │  or SQLite    │ │  (Steps 6–8)    │
     │ (deterministic)│ │  cutoffs DB   │ │  rules/FAQs     │
     └────────────────┘ └───────────────┘ └─────────────────┘
```

**Rule**: Cutoff numbers always come from the database. LLM only explains and strategizes.

## Data layer (Step 2–3)

| Stage | Location |
|-------|----------|
| Raw CSV | `data-collecting/` |
| Cleaned | `data-pipeline/merged-data/master_cutoffs_merged.csv` |
| ORM | `counselling.models` — `College`, `Program`, `Cutoff` |
| Import | `python manage.py load_master_data` |

### ER diagram (simplified)

```
College 1──* Program 1──* Cutoff
  │              │
  │              └── branch_canonical, fees, placement
  └── category (IIT/NIT/…), state, ratings
```

## Backend layout

```
backend/
├── django-app/
│   ├── config/          # settings, urls
│   └── counselling/     # models, APIs, import command
└── recommendation_engine/
    ├── engine.py        # rank → dream/target/safe
    └── schemas.py       # response dataclasses
```

## Prediction flow (Step 4–5)

1. Client `POST /api/v1/predict/` with `rank`, `category`, `gender`, optional `branch_preferences`, `home_state`.
2. `PredictionEngine` queries `Cutoff` where `closing_rank >= rank` for latest year/round.
3. Each row classified: **DREAM** (borderline), **TARGET**, **SAFE** by margin ratio.
4. JSON returned; Gemini (later) receives this JSON as context — never invents ranks.

## Preference order (Step 9 — partial)

`POST /api/v1/preferences/generate/` uses `counselling.services.generate_preference_order`:

1. Safe anchors (top 3)
2. Target colleges
3. Dream picks
4. Remaining safe backups

## Local development

```powershell
cd backend/django-app
..\..\..venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py load_master_data   # ~6 min first time
python manage.py runserver
```

- Health: `GET http://127.0.0.1:8000/api/v1/health/`
- Predict: `POST http://127.0.0.1:8000/api/v1/predict/` with JSON body

## PostgreSQL (production)

```powershell
cd deployment
docker compose up -d
```

Set in `.env`:

```
DATABASE_URL=postgresql://josaa:josaa@localhost:5432/josaa_copilot
```

Re-run `migrate` and `load_master_data`.

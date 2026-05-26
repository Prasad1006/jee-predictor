# Backend — JoSAA Counselling Copilot

## Setup

```powershell
cd c:\Users\prasa\OneDrive\Desktop\jee-predictor-copilot
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd backend\django-app
python manage.py migrate
python manage.py load_master_data    # ~6 minutes, 459k cutoffs
python manage.py test counselling
python manage.py runserver
```

API base: http://127.0.0.1:8000/api/v1/

See [docs/API_SPECIFICATION.md](../docs/API_SPECIFICATION.md).

## PostgreSQL

```powershell
cd deployment
docker compose up -d
```

Copy `.env.example` to `.env` and set:

```
DATABASE_URL=postgresql://josaa:josaa@localhost:5432/josaa_copilot
```

Then `migrate` + `load_master_data` again.

## Structure

| Path | Purpose |
|------|---------|
| `django-app/counselling/` | Models, REST views, data import |
| `recommendation_engine/` | Deterministic rank predictor |

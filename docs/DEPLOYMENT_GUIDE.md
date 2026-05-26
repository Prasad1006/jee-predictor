# Deployment Guide (Step 10)

## Local development (full stack)

```powershell
# Terminal 1 — API
cd backend\django-app
..\..\..venv\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2 — Frontend (requires Node.js 18+)
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

- API: http://127.0.0.1:8000/api/v1/health/
- UI: http://localhost:3000

## Environment variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `GEMINI_API_KEY` | Backend `.env` | Full AI chat responses |
| `DATABASE_URL` | Backend `.env` | PostgreSQL (optional) |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | Production API URL |
| `SECRET_KEY` | Backend `.env` | Django secret |
| `CORS_ALLOWED_ORIGINS` | Backend `.env` | Frontend domain |

## PostgreSQL (production)

```powershell
cd deployment
docker compose up -d
```

Set `DATABASE_URL=postgresql://josaa:josaa@localhost:5432/josaa_copilot`, then:

```powershell
python manage.py migrate
python manage.py load_master_data
python manage.py ingest_knowledge
```

## Suggested hosting

| Component | Service |
|-----------|---------|
| Frontend | [Vercel](https://vercel.com) — root `frontend/` |
| Django API | [Railway](https://railway.app) or [Render](https://render.com) |
| PostgreSQL | Neon, Supabase, or Railway addon |
| ChromaDB | Persistent volume on API host, or embedded path in `datasets/embeddings` |

## Vercel (frontend)

- Framework: Next.js
- Root directory: `frontend`
- Env: `NEXT_PUBLIC_API_URL=https://your-api.example.com/api/v1`

## Railway (backend)

- Start command: `cd backend/django-app && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Add `requirements.txt` at repo root
- Run release command: `python manage.py migrate`

## Pre-launch checklist

- [ ] `DEBUG=false` in production
- [ ] Strong `SECRET_KEY`
- [ ] CORS allows only your frontend domain
- [ ] `GEMINI_API_KEY` set securely
- [ ] Database backed up
- [ ] Disclaimer visible: verify on josaa.nic.in

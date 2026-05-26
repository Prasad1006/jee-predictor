# AI JoSAA Counselling Copilot — Developer Handoff

**Purpose**: Onboard the next developer. Shows what is done, what is in progress, and exactly what to do for each of the 10 execution steps.

**Last updated**: May 24, 2026  
**Overall progress**: **8 / 10 complete** (Steps 1–8 done; Step 9 partial; deploy next)

---

## Quick status

| Step | Name | Status | Owner action |
|------|------|--------|--------------|
| 1 | Analyze existing datasets | ✅ **Done** | Read reports only |
| 2 | Build data cleaning pipeline | ✅ **Done** | Review `quality/quality_report.json`; spot-check mappings |
| 3 | Create master counselling database | ✅ **Done** | `manage.py load_master_data` — SQLite default, PostgreSQL via `.env` |
| 4 | Build recommendation engine | ✅ **Done** | `backend/recommendation_engine/` |
| 5 | Build Django APIs | ✅ **Done** | `backend/django-app/` — see `API_SPECIFICATION.md` |
| 6 | Build RAG pipeline | ✅ **Done** | ChromaDB + seed FAQs; `manage.py ingest_knowledge` |
| 7 | Build Next.js frontend | ✅ **Done** | `frontend/` — run `npm install && npm run dev` (needs Node.js) |
| 8 | Build AI counselling assistant | ✅ **Done** | `POST /api/v1/chat/` + `ai_engine/orchestrator.py` |
| 9 | Build preference order generator | 🟡 **Partial** | API exists; tune tiers + Gemini explanations |
| 10 | Deploy & scale | ⬜ **Next** | Vercel + Railway + managed PostgreSQL |

---

## Repository layout (current vs target)

### What exists today

```
jee-predictor-copilot/
├── data-collecting/          # Raw CSVs (4 files in repo)
├── data-pipeline/
│   ├── mappings/             # Canonical JSON mappings (Step 1)
│   ├── *.py                  # Analysis + cleaning scripts
│   ├── cleaned-data/         # Created by Step 2 pipeline
│   ├── standardized-data/
│   ├── normalized-data/
│   ├── merged-data/
│   └── quality/
├── docs/                     # This file + step guides
└── .venv/                    # Python 3 + pandas, openpyxl
```

### Created (Steps 3–5)

```
backend/
  django-app/           # Django 5 + DRF
  recommendation_engine/
deployment/docker-compose.yml   # PostgreSQL
```

### Not created yet (Steps 6–7, 10)

```
frontend/         # Next.js 15 + TypeScript
ai-engine/        # RAG, Gemini, ChromaDB
datasets/         # counselling-rules PDFs
```

### Raw data note

The product vision lists many XLSX/CSV files (2021–2024 rounds, seat matrix, etc.). **Only 4 CSVs are currently in `data-collecting/`**. Add missing files there (or under `datasets/cutoffs/`) and extend `clean_raw_data.py` to ingest them before claiming full historical coverage.

| File | In repo? |
|------|----------|
| `merged_jee_cutoff_2018_2025.csv` | ✅ |
| `data.csv` | ✅ |
| `College_data.csv` | ✅ |
| `Top_Indian_Colleges_Fees_Placement.csv` | ✅ |
| `2021Round1.xlsx` … `2024_Round_*.csv` etc. | ❌ Add when available |

---

## Step 1 — Analyze existing datasets ✅ DONE

### Goal

Understand schemas, conflicts, duplicates, and naming issues across all counselling data.

### What was done

- Ran `data-pipeline/analyze_datasets.py`, `inspect_datasets.py`, `get_unique_values.py`, `extract_colleges.py`
- Produced `data-collecting/data_analysis_report.json`
- Created canonical mapping templates in `data-pipeline/mappings/`:
  - `canonical_categories.json`, `canonical_quotas.json`, `canonical_gender.json`
  - `canonical_branches.json`, `canonical_states.json`
- Extracted **3,330** unique college names → `all_colleges_to_canonicalize.json`
- Wrote `docs/DATA_NORMALIZATION_PLAN.md`, `docs/STEP1_COMPLETION_REPORT.md`

### Key findings (keep in mind for cleaning)

- ~505K cutoff rows (merged file dominates)
- College names: IIT/NIT/IIIT vs full names vs typos
- Categories: `GEN` vs `OPEN`, PwD variants
- Quotas: `AI`, `HS`, `OS`, state-specific (`AP`, `JK`, …)
- Programs: verbose JoSAA strings need branch parsing

### Next developer

- **No work required** unless new raw files are added → re-run Step 1 scripts and update mappings.

---

## Step 2 — Build data cleaning pipeline ✅ DONE

### Goal

Normalize raw data → cleaned CSVs ready for PostgreSQL.

### What was done

- Runnable pipeline: `python data-pipeline/run_pipeline.py`
- Scripts: `auto_populate_colleges.py`, `clean_raw_data.py`, `standardize_columns.py`, `normalize_colleges.py`, `merge_and_deduplicate.py`, `validate_data.py`
- **459,407** unified cutoff rows in `data-pipeline/merged-data/master_cutoffs_merged.csv`
- Quality report: `data-pipeline/quality/quality_report.json` — all gates **passed** (May 24, 2026)

### Latest quality metrics

| Check | Result |
|-------|--------|
| Valid rank ranges | 99.97% |
| College name matched | 100% |
| Years covered | 2016–2025 |
| Duplicates removed | 39,544 |

### Optional follow-up

1. Manually spot-check `mappings/colleges_auto_mapped.json` for top IIT/NIT names (fuzzy match can over-merge).
2. Add missing round XLSX files to `data-collecting/` and re-run pipeline.
3. Improve `branch_canonical` coverage (~0.63% still unmapped).

### Quality gates

| Metric | Target |
|--------|--------|
| Valid rank ranges (`opening ≤ closing`) | ≥ 99% |
| College name matched (exact or fuzzy) | ≥ 95% |
| Critical columns non-null | ≥ 99% |
| Manual review queue | < 100 unique institutes |

### Outputs

| Path | Description |
|------|-------------|
| `data-pipeline/cleaned-data/` | Trimmed columns, lowercase names |
| `data-pipeline/standardized-data/` | Categories, quotas, gender applied |
| `data-pipeline/normalized-data/` | Canonical college names |
| `data-pipeline/merged-data/master_cutoffs_merged.csv` | Unified cutoff table |
| `data-pipeline/quality/quality_report.json` | QA metrics |

---

## Step 3 — Create master counselling database ✅ DONE

### Goal

Single PostgreSQL schema for cutoffs, colleges, programs, fees, placements, seat matrix.

### What was done

- Django models: `College`, `Program`, `Cutoff` in `backend/django-app/counselling/models.py`
- Import: `python manage.py load_master_data` (~444k cutoffs, 3229 colleges loaded)
- Default DB: SQLite at `backend/django-app/db.sqlite3`
- PostgreSQL: `deployment/docker-compose.yml` + `DATABASE_URL` in `.env`

### Original tasks (reference)

1. **Design schema** (implemented):

   - `colleges` — id, canonical_name, category (IIT/NIT/…), state, city, nirf_rank
   - `programs` — id, college_id, branch_code, full_name, degree, duration
   - `cutoffs` — college_id, program_id, year, round, category, quota, gender, opening_rank, closing_rank
   - `placements` — college_id, avg_package, placement_rate, year
   - `fees` — college_id, program_id, tuition, hostel
   - `seat_matrix` — year, college_id, program_id, seats by category/quota

2. **Create Django project** under `backend/django-app/` (or standalone SQL migrations in `data-pipeline/postgres-importers/`).

3. **Import scripts**:
   - Load from `merged-data/master_cutoffs_merged.csv`
   - Load `College_data.csv` + fees/placement CSV into dimension tables

4. **Indexes**: `(year, category, quota, closing_rank)`, `(college_id, program_id, year, round)`

5. **Validation queries**: row counts, orphan programs, rank sanity checks

### Deliverables

- `backend/postgres-models/` or Django models
- `data-pipeline/postgres-importers/load_master_db.py`
- ER diagram in `docs/ARCHITECTURE.md` (optional)
- DB dump or migration files

### Estimated effort

1–2 days

---

## Step 4 — Build recommendation engine ✅ DONE

### Goal

**Deterministic** rank → college predictions (AI only explains; does not invent cutoffs).

### What was done

- `backend/recommendation_engine/engine.py` — `PredictionEngine`, `PredictionRequest`
- Tier logic: DREAM / TARGET / SAFE from closing-rank margin
- Unit test: `counselling/tests.py`

### Original tasks

1. Create `backend/recommendation_engine/` module:

   - Input: `rank`, `category`, `gender`, `home_state`, `branch_preferences[]`, `quota` (HS/OS/AI logic)
   - Filter cutoffs where `closing_rank >= student_rank` (JoSAA convention: lower rank number = better)
   - Classify each option: **Dream** / **Target** / **Safe** using margin vs closing rank and round trends
   - Round prediction: compare same seat across rounds 1→6 where data exists
   - State quota: prefer HS seats when student state matches institute state

2. Probability score (heuristic, not ML v1):

   - `margin = closing_rank - student_rank`
   - Buckets: safe if margin > 20%, target if 0–20%, dream if negative

3. Unit tests with known ranks (e.g. 18k OBC, Telangana → expect NIT/IIIT mix)

### Deliverables

- `predictor.py` (or `engine.py`) + tests
- JSON schema for prediction response (used by APIs and AI layer)

### Estimated effort

3–4 days

---

## Step 5 — Build Django APIs ✅ DONE

### Goal

REST APIs for frontend and AI orchestration.

### What was done

Endpoints live under `/api/v1/` — full spec in `docs/API_SPECIFICATION.md`.

| Endpoint | Status |
|----------|--------|
| `POST /predict/` | ✅ |
| `POST /preferences/generate/` | ✅ |
| `GET /colleges/{id}/` | ✅ |
| `GET /colleges/compare/` | ✅ |
| `GET /meta/` | ✅ |
| `GET /health/` | ✅ |
| `POST /chat/` | ✅ |

### Original tasks

1. Scaffold `backend/django-app/`:
   - Django 5 + DRF + `django-cors-headers`
   - PostgreSQL settings from env
   - Redis + Celery (optional for v1, required for heavy jobs)

2. **Endpoints** (minimum):

   | Method | Path | Purpose |
   |--------|------|---------|
   | POST | `/api/v1/predict/` | Rank → college list + tiers |
   | POST | `/api/v1/preferences/generate/` | Optimized choice list (Step 9 logic) |
   | GET | `/api/v1/colleges/{id}/` | College detail |
   | GET | `/api/v1/colleges/compare/?ids=1,2,3` | Side-by-side stats |
   | GET | `/api/v1/meta/categories/` | Categories, quotas, branches |

3. OpenAPI / drf-spectacular for frontend codegen

4. Auth: optional for MVP; JWT for saved preferences later

### Deliverables

- `docs/API_SPECIFICATION.md`
- Running server + Postman collection or OpenAPI URL

### Estimated effort

3–4 days

---

## Step 6 — Build RAG pipeline ✅ DONE

### What was done

- `ai_engine/rag/` — chunking, ChromaDB ingest, retriever (keyword fallback if Chroma unavailable)
- Seed docs: `datasets/counselling-rules/josaa_faq.md`, `choice_filling_strategy.md`
- Command: `python manage.py ingest_knowledge` (8 chunks embedded)
- Persist path: `datasets/embeddings/`

### Add more sources

Drop `.md` / `.txt` / PDFs (parse to text first) into `datasets/counselling-rules/` and re-run ingest.

### Original tasks

1. `ai_engine/rag/`:
   - Parse PDFs (PyMuPDF or LlamaParse)
   - Chunk (~500 tokens, overlap 50)
   - Embed with Gemini or `text-embedding-004`
   - Store in **ChromaDB** (`datasets/embeddings/`)

2. Retriever: top-k similarity + metadata filters (e.g. `doc_type=josaa_rules`)

3. `ai-engine/gemini-integration/`: structured prompt template

### Architecture rule

```
User question
  → classify (cutoff vs rules vs strategy)
  → if cutoff: call Django predict API
  → if rules: RAG retrieve
  → Gemini 2.5 Flash synthesizes with BOTH contexts
```

### Deliverables

- Ingest script + Chroma persistence
- `retrieve_context(query) -> chunks[]`

### Estimated effort

2–3 days

---

## Step 7 — Build Next.js frontend ✅ DONE

### What was done

- `frontend/` — Next.js 15 App Router, Tailwind, pages: `/`, `/predictor`, `/chat`
- API client: `frontend/lib/api.ts` → `NEXT_PUBLIC_API_URL`
- **Requires Node.js**: `cd frontend && npm install && npm run dev`

### Original tasks

1. `npx create-next-app@latest frontend` — App Router, TypeScript, Tailwind

2. **Pages**:
   - `/` — hero + feature links
   - `/predictor` — rank form → results (React Query → `/api/v1/predict/`)
   - `/chat` — counselling UI (streaming later)
   - `/compare` — multi-college comparison
   - `/guides/[slug]` — SEO content (SSR)

3. Components: `CollegeCard`, `TierBadge`, `RankForm`, chat layout

4. SEO: `metadata`, `sitemap.ts`, static pages for “best NITs for CSE under 10k rank”

### Tech

Next.js 15, Shadcn UI, Framer Motion, React Query

### Estimated effort

4–5 days

---

## Step 8 — Build AI counselling assistant ✅ DONE

### What was done

- `ai_engine/orchestrator.py` — intent detection, DB predictions, RAG, Gemini
- `POST /api/v1/chat/` — works **offline** without API key; set `GEMINI_API_KEY` for full AI
- System prompt: `ai_engine/prompts/counselling_system.txt`

### Original tasks

1. `ai-engine/reasoning-engine/` orchestrator:
   - Intent detection (predict / compare / preference / general FAQ)
   - Tool calls to Django APIs
   - Inject RAG chunks for policy questions
   - Conversation memory (Redis or DB session)

2. **Do not** pass raw cutoffs only to Gemini — always attach structured API JSON

3. Safety: disclaimers, “verify on josaa.nic.in”, no guaranteed admission claims

### Deliverables

- `POST /api/v1/chat/` (Django proxies to ai-engine or monolith module)
- System prompt v1 in `ai-engine/prompts/counselling_system.txt`

### Estimated effort

2–3 days

---

## Step 9 — Build preference order generator ⬜ NOT STARTED

### Goal

JoSAA choice-filling order with strategic risk balancing and explanations.

### Prerequisites

- Step 4 prediction tiers
- Step 8 for natural-language “why”

### Algorithm (v1 heuristic)

1. Bucket colleges from predict API into dream / target / safe
2. Sort within bucket by student priority (branch > college tier > location)
3. Interleave: avoid all-dream at top → use pattern like safe anchor → targets → dreams → upgrades
4. Enforce branch priority (CSE > ECE if user said so)
5. Cap list length (e.g. 50–100 choices)
6. Gemini explains each block (optional API field `explanation`)

### Deliverables

- `preference_generator.py` in recommendation-engine
- `POST /api/v1/preferences/generate/`
- Frontend page `/preference-generator`

### Estimated effort

2 days

---

## Step 10 — Deploy & scale ⬜ NOT STARTED

### Goal

Production before 2026 JoSAA season.

### Target stack

| Component | Service |
|-----------|---------|
| Frontend | Vercel |
| Django API | Railway or Render |
| PostgreSQL | Managed (Neon / Supabase / RDS) |
| Redis | Upstash or managed Redis |
| Celery workers | Same host as API or separate worker service |
| ChromaDB | Hosted or persistent volume |
| Secrets | Platform env vars — never commit `.env` |

### Tasks

1. `deployment/docker-compose.yml` for local prod parity
2. CI: lint + test on PR (GitHub Actions)
3. Monitoring: Sentry, health checks `/api/health/`
4. CDN + caching for static SEO pages
5. Rate limits on Gemini and public APIs

### Deliverables

- `docs/DEPLOYMENT_GUIDE.md`
- Staging + production URLs documented

### Estimated effort

2–3 days

---

## AI architecture (mandatory for all steps)

```
┌─────────────────────────────────────────────────────────┐
│  Student message                                         │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│  Orchestrator (Step 8)                                   │
│  • Intent → Django APIs (cutoffs) OR RAG (rules)        │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌──────────────────┐  ┌──────────────────┐  ┌────────────┐
│ PostgreSQL       │  │ ChromaDB RAG     │  │ Gemini 2.5 │
│ (facts)          │  │ (policies/FAQs)  │  │ Flash      │
└──────────────────┘  └──────────────────┘  └────────────┘
                            ▼
                   Final counselling response
```

**Never** rely on Gemini alone for cutoff numbers.

---

## Environment variables (future)

```env
# Database
DATABASE_URL=postgresql://...

# AI
GEMINI_API_KEY=
CHROMA_PERSIST_DIR=./datasets/embeddings

# Django
SECRET_KEY=
DEBUG=false
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=

# Frontend
NEXT_PUBLIC_API_URL=https://api.example.com
```

---

## Commands cheat sheet

```powershell
# Step 1 (already run)
python data-pipeline/analyze_datasets.py

# Step 2
python data-pipeline/run_pipeline.py

# Step 3 (after implemented)
python data-pipeline/postgres-importers/load_master_db.py

# Backend (after scaffold)
cd backend/django-app
python manage.py runserver

# Frontend (after scaffold)
cd frontend
npm run dev
```

---

## Related documentation

| Document | Use when |
|----------|----------|
| [PROJECT_ROADMAP.md](./PROJECT_ROADMAP.md) | Executive timeline & architecture diagram |
| [STEP1_COMPLETION_REPORT.md](./STEP1_COMPLETION_REPORT.md) | Detailed Step 1 findings |
| [DATA_NORMALIZATION_PLAN.md](./DATA_NORMALIZATION_PLAN.md) | Field-level normalization rules |
| [STEP2_IMPLEMENTATION_GUIDE.md](./STEP2_IMPLEMENTATION_GUIDE.md) | Script-level Step 2 detail |
| **DEVELOPER_HANDOFF.md** (this file) | **Start here** |

---

## Immediate next actions (priority order)

1. ✅ Read this document
2. **Run full stack locally:**
   - Terminal 1: `cd backend/django-app && python manage.py runserver`
   - Terminal 2: `cd frontend && npm install && npm run dev` (install Node.js if needed)
3. Copy `.env.example` → `.env` and set `GEMINI_API_KEY` for AI chat
4. ⬜ **Step 10** — Deploy (Vercel + Railway)
5. ⬜ Add JoSAA PDFs to `datasets/counselling-rules/` and `ingest_knowledge`
6. ⬜ Improve `load_master_data` program coverage (~1.7k programs today)

---

## Contact / handoff notes from Copilot session

- GitHub Copilot completed **Step 1** fully and prepared **Step 2** guides + mappings but hit usage limit before implementing runnable cleaning scripts.
- Cursor session continued: added `run_pipeline.py` + cleaning scripts and this handoff doc.
- College canonicalization for 3,330 institutes is **partially automated**; top IIT/NIT/IIIT should be manually verified once before production.

**Questions?** Update this file when a step status changes so the next developer never has to guess.

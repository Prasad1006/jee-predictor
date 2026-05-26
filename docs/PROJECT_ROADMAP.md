# AI JoSAA Counselling Copilot - Executive Roadmap & Status Report

**Project**: AI-Powered JoSAA Counselling Platform for JEE Main Students  
**Vision**: "ChatGPT for JoSAA Counselling"  
**Start Date**: May 24, 2026  
**Target Launch**: Before 2026 JoSAA Counselling Season  
**Status**: Phase 1–2 Complete ✅ (data pipeline ready for PostgreSQL)

---

## Project Vision & Goals

### What We're Building

An intelligent counselling platform that helps JEE Main students make confident college & branch decisions by:
- Predicting eligible colleges based on rank/category/quota
- Generating optimized JoSAA preference orders
- Comparing colleges based on placement, fees, culture
- Providing AI-powered counselling advice
- Explaining "why" behind every recommendation

### Why It Matters

Current situation:
- Students use basic rank-cutoff calculators
- No personalized counselling assistance
- Information scattered across multiple sources
- Risk of suboptimal college/branch choices

Our solution:
- Unified AI counselling assistant
- Data-driven recommendations
- Strategic preference ordering
- Confidence-building explanations

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   AI JoSAA Counselling Copilot                  │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Frontend (Next.js + TypeScript)            │    │
│  │  • Chatbot UI                                           │    │
│  │  • Predictor Dashboard                                 │    │
│  │  • College Comparison Tool                             │    │
│  │  • Preference Order Generator                          │    │
│  │  • SEO Landing Pages                                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                            ↓                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Backend APIs (Django REST Framework)                  │    │
│  │  • Rank Prediction API                                 │    │
│  │  • College Search API                                  │    │
│  │  • Preference Generation API                           │    │
│  │  • Analytics API                                       │    │
│  └────────────────────────────────────────────────────────┘    │
│           ↑                           ↑                         │
│    ┌──────────────┐           ┌──────────────┐                 │
│    │   AI Engine  │           │   Database   │                 │
│    │   (Gemini    │           │ (PostgreSQL) │                 │
│    │  + RAG +     │           │              │                 │
│    │  LLamaIndex) │           │  • Cutoffs   │                 │
│    └──────────────┘           │  • Colleges  │                 │
│    • Chatbot Logic            │  • Programs  │                 │
│    • Reasoning Engine         │  • Placement │                 │
│    • RAG Retriever            └──────────────┘                 │
│    • Explanation Gen          ↑                                 │
│                           ┌──────────────┐                     │
│                           │  Vector DB   │                     │
│                           │  (ChromaDB)  │                     │
│                           │              │                     │
│                           │  Embeddings: │                     │
│                           │  • FAQs      │                     │
│                           │  • Rules     │                     │
│                           │  • Reports   │                     │
│                           └──────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10-Step Execution Plan with Status

### ✅ PHASE 1: DATA FOUNDATION (COMPLETE)

#### Step 1: ✅ Analyze Existing Datasets  
**Status**: COMPLETE (May 24, 2026)

**Deliverables**:
- [x] Schema analysis of all 4 CSV + XLSX files
- [x] Identified 6 major data inconsistency categories
- [x] Created 5 canonical mapping templates
- [x] Extracted 3,330 unique colleges
- [x] Generated comprehensive normalization plan

**Key Findings**:
- 505,749 total records across all datasets
- 3,330 unique colleges (multiple naming formats)
- Categories: GEN vs OPEN mismatch
- Programs: Verbose naming requires parsing
- States: Spelling inconsistencies (Orissa → Odisha)

**Artifacts**:
- `DATA_NORMALIZATION_PLAN.md`
- `STEP1_COMPLETION_REPORT.md`
- Mapping files (5x JSON)
- College list (3,330 entries)

---

### 🔄 PHASE 2: DATA PIPELINE (IN PROGRESS)

#### Step 2: ✅ Build Data Cleaning Pipeline  
**Status**: COMPLETE (May 24, 2026)

**Tasks**:
- [x] Auto-populate college mappings (fuzzy matching)
- [x] Build raw data cleaning script
- [x] Standardize categories & quotas
- [x] Normalize college names
- [x] Merge datasets with deduplication
- [x] Validate data quality
- [x] Generate quality report
- [ ] Manual review of flagged records (optional spot-check)

**Estimated Duration**: 3-4 days

**Success Criteria**:
- 95%+ college matches
- 99%+ valid rank ranges
- <100 manual review items
- Quality metrics: See quality gates

**Artifacts to Create**:
- 5 Python cleaning scripts
- Cleaned CSV datasets
- Quality report JSON
- Validation log

---

#### Step 3: Create Master Counselling Database  
**Status**: NOT STARTED — **NEXT** (see `DEVELOPER_HANDOFF.md`)

**Tasks**:
- [ ] Design PostgreSQL schema
- [ ] Create master tables (colleges, programs, cutoffs, placements)
- [ ] Load cleaned data
- [ ] Create indices & optimize
- [ ] Run validation queries
- [ ] Backup & version control

**Estimated Duration**: 1-2 days

**Schema Overview**:
```sql
master_colleges (id, name, state, category, founding_year, nirf_rank)
master_programs (id, name, category, duration, degree)
master_cutoffs (college_id, program_id, year, round, category, quota, 
                gender, opening_rank, closing_rank)
master_placements (college_id, avg_package, placement_rate, top_package)
master_fees (college_id, program_id, tuition_fee, hostel_fee)
```

**Artifacts**:
- PostgreSQL dump
- ER diagram
- Index definitions
- Migration scripts

---

### 🔵 PHASE 3: BACKEND LOGIC (PLANNED)

#### Step 4: Build Recommendation Engine  
**Status**: NOT STARTED (Start: May 29, 2026 | Est. Complete: June 2, 2026)

**Components**:
- Deterministic prediction logic
- Safe/Moderate/Dream classification
- Rank filtering & quota handling
- Round prediction algorithm
- State quota advantage calculator

**Expected Output**:
- Python recommendation engine
- Probability scoring system

---

#### Step 5: Build Django APIs  
**Status**: NOT STARTED (Start: June 2, 2026 | Est. Complete: June 5, 2026)

**APIs**:
- POST /api/predict-colleges
- POST /api/generate-preferences
- GET /api/colleges/{id}/compare
- GET /api/counselling/faq
- GET /api/analytics/trends

---

### 🟣 PHASE 4: AI & RAG (PLANNED)

#### Step 6: Build RAG Pipeline  
**Status**: NOT STARTED (Start: June 5, 2026 | Est. Complete: June 7, 2026)

**Components**:
- PDF parsing (JOSAA rules, brochures)
- Embedding generation
- Vector DB (ChromaDB)
- Retriever creation
- Gemini 2.5 Flash integration

---

#### Step 8: Build AI Counselling Assistant  
**Status**: NOT STARTED (Start: June 7, 2026 | Est. Complete: June 9, 2026)

**Features**:
- Conversational interface
- Context-aware responses
- Explanation generation
- Multi-turn conversations

---

### 🟢 PHASE 5: FRONTEND (PLANNED)

#### Step 7: Build Next.js Frontend  
**Status**: NOT STARTED (Start: June 9, 2026 | Est. Complete: June 12, 2026)

**Pages**:
- Home page
- Predictor dashboard
- Chatbot interface
- College comparison
- Preference order generator
- SEO pages (30+)

**Tech Stack**:
- Next.js 15 + TypeScript
- Tailwind CSS + Shadcn UI
- React Query
- Framer Motion

---

#### Step 9: Build Preference Order Generator  
**Status**: NOT STARTED (Start: June 12, 2026 | Est. Complete: June 13, 2026)

**Features**:
- Strategic ordering algorithm
- Risk balancing
- Upgrade optimization
- Branch prioritization
- AI-generated explanations

---

### 🟠 PHASE 6: DEPLOYMENT (PLANNED)

#### Step 10: Deployment & Scaling  
**Status**: NOT STARTED (Start: June 13, 2026 | Est. Complete: June 15, 2026)

**Deployments**:
- Frontend → Vercel
- Backend → Railway/Render
- Database → PostgreSQL (managed)
- Vector DB → ChromaDB (managed)
- Caching → Redis
- Background jobs → Celery

---

## Timeline Summary

```
┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│  May    │  June   │  June   │  June   │  June   │  June   │
│  24-28  │  28-5   │  5-9    │  9-12   │  12-13  │  13-15  │
├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│  DATA   │DATABASE │  APIS   │ FRONTEND│ ADVANCED│  LAUNCH │
│ CLEANING│ & RECOMMENDATIONS       │ RAG+AI  │FEATURES │         │
│         │         │         │         │         │         │
│✅ 100%  │🟡 50%  │🔵 0%    │🟣 0%    │🟢 0%    │🟠 0%    │
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
```

**Total Duration**: ~22 days from start to launch  
**Target Launch**: June 15, 2026

---

## Resource Requirements

### Technology Stack

**Frontend**:
- Next.js 15
- TypeScript
- Tailwind CSS + Shadcn UI
- React Query
- Framer Motion

**Backend**:
- Django + DRF
- PostgreSQL
- Redis
- Celery
- Gunicorn

**AI**:
- Gemini 2.5 Flash API
- LangChain
- LlamaIndex
- ChromaDB

**DevOps**:
- Git + GitHub
- Docker
- CI/CD (GitHub Actions)
- Monitoring (Sentry)

### Team Requirements

- **Backend Engineer**: Django + PostgreSQL (1 person)
- **AI/ML Engineer**: LLM integration + RAG (1 person)
- **Frontend Engineer**: React/Next.js (1 person)
- **Data Engineer**: ETL pipeline (0.5 person)
- **QA/Testing**: Manual + Automation (0.5 person)

**Total**: 3-4 FTE

---

## Success Metrics & KPIs

### Phase 1 Metrics (DATA)
- [x] Schema conflicts identified
- [x] Normalization plan created
- [ ] 95%+ college names canonicalized
- [ ] <1% missing values in critical columns

### Phase 2-3 Metrics (PIPELINE)
- [ ] 99%+ valid rank ranges
- [ ] 100% of records processed
- [ ] <100 manual review items
- [ ] Database queries execute <100ms

### Phase 4-5 Metrics (AI & FRONTEND)
- [ ] Chatbot latency: <2 seconds
- [ ] Prediction accuracy: >90%
- [ ] Page load time: <3 seconds
- [ ] Uptime: >99.9%

### User Metrics
- [ ] Monthly active users: 10,000+
- [ ] Student satisfaction: >4.5/5
- [ ] Preference order generated: 5,000+
- [ ] Counselling sessions: 1,000+

---

## Risk Management

### High Priority Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| College name matching errors | HIGH | Fuzzy matching + manual review |
| Incomplete historical data | MEDIUM | Use multiple sources, flag gaps |
| API rate limits (Gemini) | MEDIUM | Queue management, caching |
| Database performance | HIGH | Indexing, query optimization |
| Launch timeline slippage | HIGH | Phased rollout, MVP approach |

### Mitigation Strategy
- Weekly progress reviews
- Daily standups during critical phases
- Buffer time (20%) in schedule
- Phased MVP launch (Predictor → Chatbot → Full Platform)

---

## MVP (Minimum Viable Product) - Phase 1 Rollout

**Target**: June 1, 2026

**Features**:
1. College Predictor (rank-based)
2. Safe/Moderate/Dream classification
3. Cutoff trend analysis
4. Basic comparison
5. Manual preference order input

**Not in MVP**:
- Chatbot AI
- Automated preference generation
- RAG knowledge base
- SEO pages

---

## Phase 2 Rollout (Full Feature)

**Target**: June 15, 2026

**Additional Features**:
1. AI Counselling Chatbot
2. Preference Order Generator
3. Advanced comparisons
4. Analytics & insights
5. SEO pages for organic traffic

---

## Documentation Structure

```
docs/
├── README.md
├── DEVELOPER_HANDOFF.md (start here for all 10 steps)
├── PROJECT_ROADMAP.md (this file)
├── STEP1_COMPLETION_REPORT.md
├── DATA_NORMALIZATION_PLAN.md
├── STEP2_IMPLEMENTATION_GUIDE.md
├── ARCHITECTURE.md (to be created)
├── API_SPECIFICATION.md (to be created)
├── DEPLOYMENT_GUIDE.md (to be created)
└── USER_GUIDE.md (to be created)
```

---

## How to Get Started

### For Step 2 Implementation

1. **Create auto-mapping script**:
   ```bash
   python data-pipeline/auto_populate_colleges.py
   ```

2. **Run data cleaning pipeline**:
   ```bash
   python data-pipeline/clean_raw_data.py
   python data-pipeline/standardize_categories.py
   python data-pipeline/normalize_colleges.py
   python data-pipeline/merge_and_deduplicate.py
   python data-pipeline/validate_data.py
   ```

3. **Review quality report**:
   ```bash
   cat data-pipeline/quality/quality_report.json
   ```

4. **Manual review** (if needed):
   - Check `data-pipeline/quality/validation_errors.log`
   - Review unmatched colleges
   - Update mappings

### Progress Tracking

- Use `manage_todo_list` tool to track daily progress
- Update status after each step completion
- Generate weekly status reports
- Monitor quality metrics continuously

---

## Next Steps (Immediate)

**Week 1 (May 24-28)**:
1. ✅ Complete Step 1 Analysis (DONE)
2. 🟡 Start Step 2: Data Cleaning Pipeline
3. Create auto-mapping scripts
4. Run initial cleaning
5. Quality review

**Week 2 (May 28 - June 2)**:
1. Finish data cleaning
2. Load into PostgreSQL
3. Start recommendation engine
4. Design API contracts

**Week 3+ (June 2+)**:
1. Build Django APIs
2. Develop RAG pipeline
3. Create Next.js frontend
4. Integrate AI assistant

---

## Questions & Support

For questions about:
- **Data**: See `DATA_NORMALIZATION_PLAN.md`
- **Architecture**: See `ARCHITECTURE.md` (to be created)
- **Implementation**: See step-specific guides
- **Deployment**: See `DEPLOYMENT_GUIDE.md` (to be created)

---

**Last Updated**: May 24, 2026  
**Status**: ✅ Steps 1–2 Complete — begin Step 3 (PostgreSQL)  
**Next Review**: After Step 3 database load  
**Target Completion**: June 15, 2026

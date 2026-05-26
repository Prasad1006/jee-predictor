# API Specification (v1)

Base URL: `http://localhost:8000/api/v1/`

## Health

`GET /health/`

```json
{
  "status": "ok",
  "colleges": 3229,
  "cutoffs": 444687
}
```

## Metadata

`GET /meta/`

Returns available years, categories, quotas, genders, sample branches.

---

## Predict colleges

`POST /predict/`

### Request

```json
{
  "rank": 18000,
  "category": "OBC",
  "gender": "GENDER_NEUTRAL",
  "home_state": "Telangana",
  "branch_preferences": ["COMPUTER_SCIENCE", "CSE"],
  "year": 2024,
  "round": 6,
  "quotas": ["ALL_INDIA", "HOME_STATE"],
  "limit": 50
}
```

| Field | Required | Notes |
|-------|----------|-------|
| rank | yes | JEE Main rank (lower = better) |
| category | yes | `GENERAL`, `OBC`, `SC`, `ST`, `EWS`, or `GEN`/`OPEN` aliases |
| gender | no | Default `GENDER_NEUTRAL` |
| home_state | no | Used to sort HS quota colleges |
| branch_preferences | no | Substring match on `branch_canonical` |
| year | no | Defaults to latest in DB |
| round | no | Defaults to 6 |
| limit | no | Max per tier (default 50) |

### Response

```json
{
  "rank": 18000,
  "seat_category": "OBC",
  "gender": "GENDER_NEUTRAL",
  "year": 2024,
  "home_state": "Telangana",
  "total_eligible": 120,
  "dream": [{ "college_name": "...", "tier": "DREAM", "closing_rank": 18500, "probability_score": 0.42 }],
  "target": [],
  "safe": []
}
```

Each item includes: `college_id`, `program_id`, `program_name`, `branch`, `quota`, `opening_rank`, `closing_rank`, `tier`, `margin`, `probability_score`, `rating`.

---

## Generate preference order

`POST /preferences/generate/`

Same body as predict, plus optional `max_choices` (default 50).

### Response

```json
{
  "rank": 18000,
  "seat_category": "OBC",
  "year": 2024,
  "total_choices": 50,
  "strategy": "safe_anchors_then_target_dream_interleave",
  "choices": [
    {
      "order": 1,
      "college": "NIT Warangal",
      "program": "...",
      "branch": "COMPUTER_SCIENCE_AND_ENGINEERING",
      "tier": "SAFE",
      "closing_rank": 25000,
      "quota": "ALL_INDIA",
      "why": "Safe anchor — protects against unfavourable sliding..."
    }
  ]
}
```

---

## College detail

`GET /colleges/{id}/`

Returns college profile + programs.

---

## Compare colleges

`GET /colleges/compare/?ids=1,2,3`

Returns array of college objects.

---

## AI counselling chat

`POST /chat/`

### Request

```json
{
  "message": "I got 18k OBC rank Telangana, best CSE colleges?",
  "rank": 18000,
  "category": "OBC",
  "home_state": "Telangana",
  "branch_preferences": ["CSE"],
  "history": [
    { "role": "user", "content": "..." },
    { "role": "model", "content": "..." }
  ]
}
```

### Response

```json
{
  "reply": "...",
  "intent": "predict",
  "context_used": {
    "has_predictions": true,
    "rag_sources": ["josaa_faq.md"],
    "gemini_enabled": false
  }
}
```

Set `GEMINI_API_KEY` in `.env` for full Gemini responses. Without it, replies use structured DB data + RAG text (offline mode).

---

## Example (PowerShell)

```powershell
Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/v1/predict/" `
  -ContentType "application/json" `
  -Body '{"rank":18000,"category":"OBC","home_state":"Telangana","branch_preferences":["CSE"]}'
```

# Frontend — JoSAA Counselling Copilot

Next.js 15 + TypeScript + Tailwind.

## Prerequisites

- Node.js 18+ and npm
- Django API running on port 8000

## Setup

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing |
| `/predictor` | Rank → college list |
| `/chat` | AI counselling chat |

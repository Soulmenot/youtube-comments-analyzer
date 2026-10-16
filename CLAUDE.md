# YouTube Comments Analyzer

Paste a YouTube URL, get an analysis of the video's comments (sentiment, topics, questions, spam/toxicity, most representative comments).

## Pipeline

```
URL -> validate -> scrape comments (max 1000) -> Jev classifies each comment -> aggregate (EDA) -> analysis -> frontend
```

1. **Validate URL**: accept only YouTube video URLs (`youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`, `youtube.com/embed/`). Extract the 11-char video ID with a strict regex. Reject everything else with HTTP 422. Never fetch arbitrary user-supplied URLs (SSRF).
2. **Scrape comments**: YouTube Data API v3 `commentThreads.list` (100 per page, `order=relevance`), stop at **1000 comments max** (`MAX_COMMENTS`). The API is primary; bs4 is a fallback only (comments are JS-rendered, so bs4 alone is unreliable).
3. **Decide with Jev**: each comment is sent to Jev as the `state` with a fixed set of typed questions. Jev returns typed answers and probabilities, not text.
4. **Aggregate (EDA)**: plain Python (and optionally pandas) computes distributions, means, rankings and top comments from Jev's answers. No LLM text generation anywhere.
5. **Respond**: return the typed analysis; the frontend renders charts and tables.

## Jev (TypeSafe) - the decision engine

Docs: https://docs.typesafe.ai/introduction . Jev is a "System One" model: it evaluates typed *questions* against a *state* and returns structured results (no text generation, no parsing). Because it cannot write prose, all "analysis" is classification + aggregation. Any narrative summary must be templated from the numbers in code.

- SDK: `typesafe-sdk` (import `typesafe_sdk`), Python 3.10+. Install: `pip install typesafe-sdk`.
- Use `AsyncTypeSafeClient` (`async with`, `await client.system_one(state=..., questions=...)`).
- Question types: `Noul` (yes/no probability 0..1), `Choice` (pick one, with probabilities), `Score` (graded scale with `criteria`).
- Read answers via `response.nouls[name].noul`, `response.choices[name].choice` / `.probabilities`, `response.scores[name].score`.
- Optionally pass a Pydantic `response_model` (subclass `SystemOneResponse`) for typed results.
- Model: pin a version (`jev-1.13.0`) via `TYPESAFE_DEFAULT_MODEL`; `jev-latest` is an alias that moves on release and would shift thresholds. `jev-preview` is the newest.
- Limits: 64k tokens per request, 32k per question. Billed on input tokens only (~$0.042 / Mtok). Rate limits are per org; 429s are retried by the SDK honoring `retry-after` (`RetryPolicy(max_retries=3)` default). HTTP timeout default 10s.
- English works best; other languages are less accurate. Input is text only.

### Per-comment questions (defined once in `services/analyzer.py`)

| Key | Type | Purpose |
|---|---|---|
| `sentiment` | `Score` (very negative ... very positive) | sentiment distribution and mean |
| `topic` | `Choice` (praise, criticism, question, suggestion, joke/meme, off-topic) | theme breakdown |
| `is_question` | `Noul` | surface viewer questions |
| `is_spam` | `Noul` | spam/self-promo filter |
| `is_toxic` | `Noul` | toxicity rate |

Keep the question set small and stable; each question adds input tokens per comment. Tune instructions, not code, when results look off.

### Calling pattern

- One `system_one` call per comment, run concurrently with `asyncio.gather` behind a `Semaphore` (start at ~16, tune against the org rate limit). 1000 comments with ~5 questions is cheap.
- Truncate each comment (e.g. 1000 chars) before sending. Skip empty comments; dedupe exact duplicates.
- A failed comment must not fail the request: record it as `unclassified`, report the count in the response.
- Exclude comments with `is_spam > 0.5` from sentiment/topic aggregates but report the spam rate.
- Weight optional "likes-weighted sentiment" by `like_count` alongside the unweighted mean.

## Stack

- **Backend** (`backend/`): Python 3.11+, FastAPI, Pydantic v2, Uvicorn, `typesafe-sdk` (Jev), `google-api-python-client` (YouTube Data API), bs4 (fallback only)
- **Frontend** (`frontend/`): Next.js (App Router, TypeScript), Tailwind CSS

## Planned layout

```
backend/
  app/
    main.py            # FastAPI app, CORS, routers
    config.py          # pydantic-settings, env vars
    api/routes.py      # POST /api/analyze, GET /api/health
    schemas.py         # Pydantic request/response models
    services/
      url_validator.py # URL -> video_id
      scraper.py       # comment fetching (YouTube API, bs4 fallback)
      analyzer.py      # Jev questions + concurrent classification
      aggregate.py     # EDA: distributions, means, top comments
  tests/
  requirements.txt
frontend/
  app/                 # page.tsx, layout.tsx
  components/          # UrlForm, AnalysisView, charts, LoadingState, ErrorBanner
  lib/api.ts           # typed fetch client
```

## Commands

```
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest

# Frontend
cd frontend
npm install
npm run dev        # http://localhost:3000
npm run lint
npm run build
```

## Environment variables

Backend `.env` (never commit):
- `YOUTUBE_API_KEY`
- `TYPESAFE_API_KEY` (from https://console.typesafe.ai/keys; the SDK reads it automatically)
- `TYPESAFE_DEFAULT_MODEL=jev-1.13.0`
- `MAX_COMMENTS=1000`
- `JEV_CONCURRENCY=16`
- `CORS_ORIGINS=http://localhost:3000`

Frontend `.env.local`:
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

Keep API keys server-side only; the frontend must never see them.

## API contract

`POST /api/analyze` body `{ "url": string }`

Responses:
- `200` analysis: video metadata, comments analyzed / unclassified / spam counts, sentiment distribution + mean (plain and like-weighted), topic breakdown, question rate and top questions, toxicity rate, most positive / most negative / most liked comments
- `422` invalid / non-YouTube URL
- `404` video not found; `403` comments disabled
- `429` YouTube quota or Jev rate limit
- `502` upstream failure

Keep Pydantic models in `schemas.py` as the single source of truth; mirror them as TS types in `frontend/lib/`.

## Conventions

- Type hints everywhere; Pydantic models for all request/response shapes. Async endpoints; blocking SDK calls (YouTube client) go through `run_in_threadpool`.
- Keep services pure and separate from routes so they are unit-testable. Mock YouTube and Jev in tests; no real API calls in CI.
- Treat comment text as untrusted data. Jev only returns typed answers, which limits prompt-injection impact, but never interpolate comment text into question instructions; pass it only as `state`.
- Never log API keys or full comment dumps.
- Frontend: server components by default, `"use client"` only where needed; Tailwind utilities, no custom CSS unless necessary; always show loading and error states; validate URL client-side for fast feedback but trust only backend validation.
- Small, focused commits; do not commit `.env*`, `.venv`, `node_modules`, `.next`.

## Limits and guardrails

- Hard cap: 1000 comments per analysis (top-level comments; replies optional and counted toward the cap).
- YouTube Data API quota is 10,000 units/day; `commentThreads.list` costs 1 unit per page, so one analysis is about 10 units. Cache results by `video_id` (short TTL) to avoid repeat cost.
- Add basic per-IP rate limiting on `/api/analyze`.

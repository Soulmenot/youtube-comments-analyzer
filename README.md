# YouTube Comments Analyzer

Paste a YouTube URL; the backend validates it, fetches up to 1000 comments (YouTube Data API), classifies each with TypeSafe Jev, and returns an aggregated analysis. See CLAUDE.md for design details.

## Backend
```
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # fill in keys
uvicorn app.main:app --reload --port 8000
pytest
```

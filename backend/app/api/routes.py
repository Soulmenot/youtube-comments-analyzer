import time

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import Analysis, AnalyzeRequest
from app.services.aggregate import build_analysis
from app.services.analyzer import classify_comments
from app.services.jev_analyzer import classify_comments as jev_classify
from app.services.scraper import fetch_comments
from app.services.summarizer import summarize
from app.services.url_validator import extract_video_id

router = APIRouter(prefix="/api")

_cache: dict[str, tuple[float, Analysis]] = {}
_inflight: dict[str, object] = {}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/analyze", response_model=Analysis)
async def analyze(body: AnalyzeRequest) -> Analysis:
    settings = get_settings()
    video_id = extract_video_id(body.url)

    hit = _cache.get(video_id)
    if hit and time.monotonic() - hit[0] < settings.cache_ttl_seconds:
        return hit[1]

    video, comments = await fetch_comments(video_id, settings)
    # Jev is the primary classifier; Groq is the fallback when no Jev key is configured.
    classify = jev_classify if settings.typesafe_api_key else classify_comments
    results, unclassified = await classify(comments, settings)
    analysis = build_analysis(video, len(comments), results, unclassified)
    analysis.summary = await summarize(analysis, settings)
    _cache[video_id] = (time.monotonic(), analysis)
    return analysis

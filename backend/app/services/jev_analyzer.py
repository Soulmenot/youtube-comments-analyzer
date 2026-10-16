import asyncio
import logging

from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

from app.config import Settings
from app.errors import UpstreamError
from app.schemas import Comment, CommentResult

log = logging.getLogger(__name__)

SENTIMENT_LEVELS = ["very negative", "negative", "neutral", "positive", "very positive"]
TOPICS = ["praise", "criticism", "question", "suggestion", "joke or meme", "off-topic"]

QUESTIONS = {
    "sentiment": Score(
        instructions="What is the sentiment of this YouTube comment toward the video or its subject?",
        criteria=SENTIMENT_LEVELS,
    ),
    "topic": Choice(
        instructions="What is the main purpose of this YouTube comment?",
        criteria={t: None for t in TOPICS},
    ),
    "is_question": Noul(instructions="Is this comment asking a question?"),
    "is_spam": Noul(instructions="Is this comment spam, self-promotion, a scam or a bot message?"),
    "is_toxic": Noul(instructions="Is this comment toxic, hateful or abusive?"),
}


def _to_result(comment: Comment, resp) -> CommentResult:
    top = len(SENTIMENT_LEVELS) - 1
    sentiment = resp.scores["sentiment"].score / top * 2 - 1
    return CommentResult(
        comment=comment,
        sentiment=max(-1.0, min(1.0, sentiment)),
        topic=resp.choices["topic"].choice,
        is_question=resp.nouls["is_question"].noul,
        is_spam=resp.nouls["is_spam"].noul,
        is_toxic=resp.nouls["is_toxic"].noul,
    )


async def classify_comments(
    comments: list[Comment], settings: Settings
) -> tuple[list[CommentResult], int]:
    """Classify every comment with Jev. Returns (results, unclassified_count)."""
    sem = asyncio.Semaphore(settings.jev_concurrency)

    async with AsyncTypeSafeClient(
        api_key=settings.typesafe_api_key, model=settings.typesafe_default_model
    ) as client:

        async def one(c: Comment) -> CommentResult | None:
            async with sem:
                try:
                    resp = await client.system_one(
                        state={"comment": c.text[: settings.max_comment_chars]},
                        questions=QUESTIONS,
                    )
                    return _to_result(c, resp)
                except Exception as e:  # one bad comment must not fail the request
                    log.warning("jev failed for %s: %s", c.id, type(e).__name__)
                    return None

        outcomes = await asyncio.gather(*(one(c) for c in comments))

    results = [r for r in outcomes if r is not None]
    if comments and not results:
        raise UpstreamError("Jev classification failed for all comments.")
    return results, len(comments) - len(results)

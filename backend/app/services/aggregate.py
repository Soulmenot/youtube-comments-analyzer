from collections import Counter

from app.schemas import Analysis, CommentResult, SentimentSummary, VideoMeta

SPAM_THRESHOLD = 0.5
POS, NEG = 0.2, -0.2
TOP_N = 5


def build_analysis(
    video: VideoMeta,
    total_fetched: int,
    results: list[CommentResult],
    unclassified: int,
) -> Analysis:
    spam = [r for r in results if r.is_spam > SPAM_THRESHOLD]
    clean = [r for r in results if r.is_spam <= SPAM_THRESHOLD]
    n = len(clean)

    mean = sum(r.sentiment for r in clean) / n if n else 0.0
    weights = [r.comment.like_count + 1 for r in clean]
    wmean = sum(r.sentiment * w for r, w in zip(clean, weights)) / sum(weights) if n else 0.0

    sentiment = SentimentSummary(
        mean=round(mean, 4),
        like_weighted_mean=round(wmean, 4),
        positive=sum(r.sentiment > POS for r in clean),
        negative=sum(r.sentiment < NEG for r in clean),
        neutral=sum(NEG <= r.sentiment <= POS for r in clean),
    )

    return Analysis(
        video=video,
        total_fetched=total_fetched,
        classified=len(results),
        unclassified=unclassified,
        spam_count=len(spam),
        spam_rate=round(len(spam) / len(results), 4) if results else 0.0,
        toxic_rate=round(sum(r.is_toxic > 0.5 for r in clean) / n, 4) if n else 0.0,
        question_rate=round(sum(r.is_question > 0.5 for r in clean) / n, 4) if n else 0.0,
        sentiment=sentiment,
        topics=dict(Counter(r.topic for r in clean).most_common()),
        top_questions=sorted(
            (r for r in clean if r.is_question > 0.5),
            key=lambda r: r.comment.like_count,
            reverse=True,
        )[:TOP_N],
        most_positive=sorted(clean, key=lambda r: r.sentiment, reverse=True)[:TOP_N],
        most_negative=sorted(clean, key=lambda r: r.sentiment)[:TOP_N],
        most_liked=sorted(clean, key=lambda r: r.comment.like_count, reverse=True)[:TOP_N],
    )

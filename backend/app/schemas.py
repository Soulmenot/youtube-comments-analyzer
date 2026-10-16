from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    url: str


class Comment(BaseModel):
    id: str
    author: str
    text: str
    like_count: int = 0


class VideoMeta(BaseModel):
    video_id: str
    title: str
    channel: str
    thumbnail: str | None = None
    view_count: int | None = None
    comment_count: int | None = None


class CommentResult(BaseModel):
    comment: Comment
    sentiment: float  # -1 (very negative) .. 1 (very positive)
    topic: str
    is_question: float
    is_spam: float
    is_toxic: float


class SentimentSummary(BaseModel):
    mean: float
    like_weighted_mean: float
    positive: int
    neutral: int
    negative: int


class Analysis(BaseModel):
    video: VideoMeta
    total_fetched: int
    classified: int
    unclassified: int
    spam_count: int
    spam_rate: float
    toxic_rate: float
    question_rate: float
    sentiment: SentimentSummary
    topics: dict[str, int]
    top_questions: list[CommentResult]
    most_positive: list[CommentResult]
    most_negative: list[CommentResult]
    most_liked: list[CommentResult]

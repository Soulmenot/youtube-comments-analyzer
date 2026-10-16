import pytest
from fastapi.testclient import TestClient

from app.errors import InvalidURL
from app.main import app
from app.schemas import Comment, CommentResult, VideoMeta
from app.services.aggregate import build_analysis
from app.services.url_validator import extract_video_id

VID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VID}",
        f"youtube.com/watch?v={VID}&t=10",
        f"https://youtu.be/{VID}?si=x",
        f"https://www.youtube.com/shorts/{VID}",
        f"https://www.youtube.com/embed/{VID}",
    ],
)
def test_valid_urls(url):
    assert extract_video_id(url) == VID


@pytest.mark.parametrize(
    "url",
    ["", "https://example.com/watch?v=" + VID, "https://evil.com/youtube.com/watch?v=" + VID,
     "ftp://youtube.com/watch?v=" + VID, "https://www.youtube.com/watch?v=short",
     "https://www.youtube.com/"],
)
def test_invalid_urls(url):
    with pytest.raises(InvalidURL):
        extract_video_id(url)


def test_route_rejects_bad_url():
    r = TestClient(app).post("/api/analyze", json={"url": "https://example.com"})
    assert r.status_code == 422


def _res(i, sent, spam=0.0, likes=0):
    return CommentResult(
        comment=Comment(id=str(i), author="a", text="t", like_count=likes),
        sentiment=sent, topic="praise", is_question=0.0, is_spam=spam, is_toxic=0.0,
    )


def test_aggregate_excludes_spam():
    v = VideoMeta(video_id=VID, title="t", channel="c")
    a = build_analysis(v, 3, [_res(1, 1.0), _res(2, -1.0, likes=9), _res(3, 1.0, spam=0.9)], 0)
    assert a.spam_count == 1 and a.sentiment.positive == 1 and a.sentiment.negative == 1
    assert a.sentiment.mean == 0.0

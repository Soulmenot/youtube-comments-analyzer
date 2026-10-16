import html
import re

from fastapi.concurrency import run_in_threadpool
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import Settings
from app.errors import CommentsDisabled, RateLimited, UpstreamError, VideoNotFound
from app.schemas import Comment, VideoMeta

_TAG = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    text = _TAG.sub(" ", text.replace("<br>", "\n"))
    return html.unescape(text).strip()


def _fetch(video_id: str, api_key: str, max_comments: int) -> tuple[VideoMeta, list[Comment]]:
    yt = build("youtube", "v3", developerKey=api_key, cache_discovery=False)
    try:
        vids = yt.videos().list(part="snippet,statistics", id=video_id).execute()
        items = vids.get("items", [])
        if not items:
            raise VideoNotFound("Video not found.")
        v = items[0]
        stats = v.get("statistics", {})
        meta = VideoMeta(
            video_id=video_id,
            title=v["snippet"]["title"],
            channel=v["snippet"]["channelTitle"],
            thumbnail=(v["snippet"].get("thumbnails", {}).get("medium") or {}).get("url"),
            view_count=int(stats["viewCount"]) if "viewCount" in stats else None,
            comment_count=int(stats["commentCount"]) if "commentCount" in stats else None,
        )

        comments: list[Comment] = []
        seen: set[str] = set()
        token = None
        while len(comments) < max_comments:
            resp = (
                yt.commentThreads()
                .list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=min(100, max_comments - len(comments)),
                    order="relevance",
                    textFormat="plainText",
                    pageToken=token,
                )
                .execute()
            )
            for it in resp.get("items", []):
                s = it["snippet"]["topLevelComment"]["snippet"]
                text = _clean(s.get("textDisplay", ""))
                if not text or text in seen:
                    continue
                seen.add(text)
                comments.append(
                    Comment(
                        id=it["id"],
                        author=s.get("authorDisplayName", ""),
                        text=text,
                        like_count=int(s.get("likeCount", 0)),
                    )
                )
            token = resp.get("nextPageToken")
            if not token:
                break
        return meta, comments[:max_comments]
    except HttpError as e:
        status = e.resp.status
        reason = str(e)
        if status == 403 and "commentsDisabled" in reason:
            raise CommentsDisabled("Comments are disabled for this video.")
        if status == 403 and ("quota" in reason.lower() or "rateLimit" in reason):
            raise RateLimited("YouTube API quota exceeded.")
        if status == 404:
            raise VideoNotFound("Video not found.")
        raise UpstreamError(f"YouTube API error ({status}).")


async def fetch_comments(video_id: str, settings: Settings) -> tuple[VideoMeta, list[Comment]]:
    if not settings.youtube_api_key:
        raise UpstreamError("YOUTUBE_API_KEY is not configured.")
    return await run_in_threadpool(_fetch, video_id, settings.youtube_api_key, settings.max_comments)

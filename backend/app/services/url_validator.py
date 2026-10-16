import re
from urllib.parse import parse_qs, urlparse

from app.errors import InvalidURL

_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}
_PATH_PREFIXES = ("/shorts/", "/embed/", "/live/", "/v/")


def extract_video_id(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise InvalidURL("URL is empty.")
    if "://" not in raw:
        raw = "https://" + raw
    try:
        parsed = urlparse(raw)
    except ValueError:
        raise InvalidURL("Malformed URL.")
    if parsed.scheme not in ("http", "https"):
        raise InvalidURL("Only http(s) URLs are allowed.")

    host = (parsed.hostname or "").lower()
    candidate: str | None = None
    if host == "youtu.be":
        candidate = parsed.path.lstrip("/").split("/")[0]
    elif host in _HOSTS:
        if parsed.path == "/watch":
            candidate = (parse_qs(parsed.query).get("v") or [None])[0]
        else:
            for prefix in _PATH_PREFIXES:
                if parsed.path.startswith(prefix):
                    candidate = parsed.path[len(prefix):].split("/")[0]
                    break
    else:
        raise InvalidURL("Not a YouTube URL.")

    if not candidate or not _ID.match(candidate):
        raise InvalidURL("Could not find a valid YouTube video ID in the URL.")
    return candidate

"""
Transcript acquisition for VideoTranscript Pro.

Ordered fallback chain -- YouTube transcript extraction is fragile in 2026
(PO tokens, datacenter IP blocks, ToS enforcement), so we try sources in
order and log which one succeeded for ops visibility:

  1. Official YouTube Data API v3 captions
     (works for videos you own; needs YOUTUBE_API_KEY)
  2. youtube-transcript-api community extractor (breaks periodically)
  3. Paid fallback provider (Supadata) via
     TRANSCRIPT_FALLBACK_PROVIDER / TRANSCRIPT_FALLBACK_API_KEY

We NEVER fabricate a transcript: when every source fails we raise
TranscriptUnavailableError with an honest, user-facing message.
"""
import json
import logging
import os
import re
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple, Union

from ..models.state import AgentState

logger = logging.getLogger(__name__)

USER_FACING_UNAVAILABLE = (
    "Transcripts are unavailable for this video right now. "
    "The video may not have captions, or YouTube may be blocking automated "
    "extraction. Please try again later."
)


class TranscriptUnavailableError(Exception):
    """Raised when no transcript source could provide captions."""


def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from a URL (watch, youtu.be, shorts, embed, live)."""
    parsed = urllib.parse.urlparse(url)
    host = (parsed.netloc or "").lower()

    if "youtu.be" in host:
        candidate = parsed.path.lstrip("/").split("/")[0].split("?")[0]
        if candidate:
            return candidate

    qs = urllib.parse.parse_qs(parsed.query)
    if qs.get("v"):
        return qs["v"][0]

    for prefix in ("/shorts/", "/embed/", "/live/"):
        if prefix in parsed.path:
            candidate = parsed.path.split(prefix, 1)[1].split("/")[0].split("?")[0]
            if candidate:
                return candidate

    raise ValueError("Invalid YouTube URL format")


# ---------------------------------------------------------------------------
# Source 1: official YouTube Data API v3 captions (owned videos only)
# ---------------------------------------------------------------------------

def _ts_to_seconds(hours: str, minutes: str, seconds: str) -> float:
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds.replace(",", "."))


def _srt_to_entries(srt_text: str) -> List[Dict]:
    entries: List[Dict] = []
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        ts_line = next((ln for ln in lines if "-->" in ln), None)
        if not ts_line:
            continue
        m = re.match(
            r"(\d+):(\d+):([\d.,]+)\s*-->\s*(\d+):(\d+):([\d.,]+)", ts_line.strip()
        )
        if not m:
            continue
        start = _ts_to_seconds(m.group(1), m.group(2), m.group(3))
        end = _ts_to_seconds(m.group(4), m.group(5), m.group(6))
        text = " ".join(
            ln.strip()
            for ln in lines
            if ln is not ts_line and not ln.strip().isdigit()
        )
        text = re.sub(r"<[^>]+>", "", text).strip()
        if text:
            entries.append(
                {"text": text, "start": start, "duration": max(0.0, end - start)}
            )
    return entries


def _official_captions(video_id: str) -> Optional[List[Dict]]:
    """Try the official captions API. Only works for videos you own."""
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        list_url = (
            "https://www.googleapis.com/youtube/v3/captions?part=id,snippet"
            f"&videoId={urllib.parse.quote(video_id)}"
            f"&key={urllib.parse.quote(api_key)}"
        )
        with urllib.request.urlopen(list_url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        items = data.get("items", [])
        if not items:
            return None

        def _rank(item: Dict) -> tuple:
            snippet = item.get("snippet", {})
            # Prefer manually created tracks over ASR.
            return (0 if snippet.get("trackKind") != "ASR" else 1,
                    snippet.get("language", ""))

        items.sort(key=_rank)
        caption_id = items[0]["id"]
        dl_url = (
            f"https://www.googleapis.com/youtube/v3/captions/"
            f"{urllib.parse.quote(caption_id)}"
            f"?key={urllib.parse.quote(api_key)}&tfmt=srt"
        )
        with urllib.request.urlopen(dl_url, timeout=30) as resp:
            srt_text = resp.read().decode("utf-8", "replace")
        entries = _srt_to_entries(srt_text)
        return entries or None
    except Exception as exc:  # 403 for non-owned videos, quota errors, etc.
        logger.info("official captions API unavailable for %s: %s", video_id, exc)
        return None


# ---------------------------------------------------------------------------
# Source 2: youtube-transcript-api community extractor (version-tolerant)
# ---------------------------------------------------------------------------

def _to_entries_new(fetched) -> List[Dict]:
    return [
        {
            "text": s.text,
            "start": float(s.start or 0),
            "duration": float(s.duration or 0),
        }
        for s in fetched.snippets
    ]


def _to_entries_old(raw: List[Dict]) -> List[Dict]:
    return [
        {
            "text": e.get("text", ""),
            "start": float(e.get("start", 0)),
            "duration": float(e.get("duration", 0)),
        }
        for e in raw
    ]


def _community_extractor(video_id: str) -> Optional[List[Dict]]:
    """Community extractor. Tries English first, then any available track."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        logger.warning("youtube-transcript-api is not installed")
        return None

    try:
        instance = YouTubeTranscriptApi()
        new_api = hasattr(instance, "fetch")
    except Exception:
        instance, new_api = None, False

    # 1) English preferred.
    try:
        if new_api:
            return _to_entries_new(instance.fetch(video_id, languages=["en", "en-US"]))
        raw = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
        return _to_entries_old(raw)
    except Exception as exc:
        logger.info("primary transcript fetch failed for %s: %s", video_id, exc)

    # 2) Any available transcript (manual -> generated -> translatable).
    try:
        transcript_list = (
            instance.list(video_id)
            if new_api
            else YouTubeTranscriptApi.list_transcripts(video_id)
        )
        for transcript in transcript_list:
            try:
                fetched = transcript.fetch()
                if new_api:
                    return _to_entries_new(fetched)
                return _to_entries_old(fetched)
            except Exception:
                continue
    except Exception as exc:
        logger.info("transcript-list fallback failed for %s: %s", video_id, exc)

    return None


# ---------------------------------------------------------------------------
# Source 3: paid fallback provider (Supadata)
# ---------------------------------------------------------------------------

def _supadata_fallback(video_id: str, video_url: str) -> Optional[List[Dict]]:
    api_key = os.getenv("TRANSCRIPT_FALLBACK_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        query = urllib.parse.urlencode({"url": video_url, "text": "false"})
        req = urllib.request.Request(
            f"https://api.supadata.ai/v1/youtube/transcript?{query}",
            headers={"x-api-key": api_key},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data.get("content") or []
        entries = [
            {
                "text": chunk.get("text", ""),
                # Supadata reports offset/duration in milliseconds.
                "start": float(chunk.get("offset", 0)) / 1000.0,
                "duration": float(chunk.get("duration", 0)) / 1000.0,
            }
            for chunk in content
            if chunk.get("text")
        ]
        return entries or None
    except Exception as exc:
        logger.info("Supadata fallback failed for %s: %s", video_id, exc)
        return None


def _paid_fallback(video_id: str, video_url: str) -> Optional[List[Dict]]:
    provider = os.getenv("TRANSCRIPT_FALLBACK_PROVIDER", "").strip().lower()
    if provider == "supadata":
        return _supadata_fallback(video_id, video_url)
    if provider:
        logger.warning(
            "unsupported TRANSCRIPT_FALLBACK_PROVIDER=%r; skipping paid fallback",
            provider,
        )
    return None


# ---------------------------------------------------------------------------
# Public API (signatures unchanged for existing callers)
# ---------------------------------------------------------------------------

def fetch_transcript_entries(video_url: str) -> Tuple[List[Dict], str]:
    """
    Fetch timestamped transcript entries via the fallback chain.

    Returns (entries, source_name). Raises TranscriptUnavailableError when
    every source fails -- never returns fabricated content.
    """
    video_id = extract_video_id(video_url)
    chain = [
        ("youtube_data_api", lambda vid: _official_captions(vid)),
        ("community_extractor", lambda vid: _community_extractor(vid)),
        ("paid_fallback", lambda vid: _paid_fallback(vid, video_url)),
    ]
    last_error: Optional[BaseException] = None
    for source, fn in chain:
        try:
            entries = fn(video_id)
        except Exception as exc:  # noqa: BLE001 - chain must continue
            last_error = exc
            logger.info("transcript source %s errored for %s: %s", source, video_id, exc)
            continue
        if entries:
            logger.info(
                "transcript acquired: video_id=%s source=%s segments=%d",
                video_id, source, len(entries),
            )
            return entries, source
    logger.warning(
        "all transcript sources failed: video_id=%s last_error=%s",
        video_id, last_error,
    )
    raise TranscriptUnavailableError(USER_FACING_UNAVAILABLE)


def fetch_transcript(video_url_or_state: Union[str, AgentState]) -> Optional[str]:
    """
    Fetch transcript from a YouTube video URL.

    Args:
        video_url_or_state: Either a YouTube URL string or an AgentState containing the URL

    Returns:
        The transcript text if successful, None otherwise
    """
    try:
        # Handle both string URLs and AgentState
        if isinstance(video_url_or_state, dict):
            video_url = video_url_or_state['url']
        else:
            video_url = video_url_or_state

        entries, _source = fetch_transcript_entries(video_url)
        return " ".join(entry["text"] for entry in entries)
    except TranscriptUnavailableError:
        return None
    except Exception as e:
        logger.info("Error fetching transcript: %s", e)
        return None


def update_transcript_in_state(state: AgentState) -> AgentState:
    """Update the state with the fetched transcript."""
    try:
        print(f"Fetching transcript from URL: {state['url']}...")
        entries, source = fetch_transcript_entries(state['url'])

        state["transcript"] = " ".join(entry["text"] for entry in entries)
        state["transcript_entries"] = entries
        state["transcript_source"] = source
        state["status"] = "transcript_fetched"
        print(f"Transcript fetched successfully (source: {source}).")
        return state
    except TranscriptUnavailableError as exc:
        state["error"] = str(exc)
        state["status"] = "error"
        return state
    except Exception as e:
        state["error"] = str(e)
        state["status"] = "error"
        print(f"Error in transcript agent: {str(e)}")
        return state

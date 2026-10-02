"""
Short-clip moment detection for VideoTranscript Pro.

Given timestamped transcript entries, an LLM picks the top shareable moments
(strong hook, key insight, story peak) and returns timestamp ranges + titles.

Cutting actual video files is intentionally NOT done server-side: downloading
YouTube videos violates YouTube's Terms of Service. If you hold a lawful local
copy of the source video, `cut_clips_from_file` will cut the detected moments
with ffmpeg when it is installed (see DEPLOY.md).
"""
import json
import logging
import os
import shutil
import subprocess
from typing import Dict, List

logger = logging.getLogger(__name__)

DEFAULT_MAX_MOMENTS = 3
# Keep the prompt small enough for cheap, fast inference.
PROMPT_MAX_CHARS = 12000


def format_timestamp(seconds: float) -> str:
    """Format seconds as M:SS for display."""
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def _entries_to_prompt_text(entries: List[Dict], max_chars: int = PROMPT_MAX_CHARS) -> str:
    lines: List[str] = []
    total = 0
    for entry in entries:
        line = f"[{format_timestamp(entry.get('start', 0))}] {entry.get('text', '')}"
        if total + len(line) > max_chars:
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines)


def detect_clip_moments(
    entries: List[Dict], max_moments: int = DEFAULT_MAX_MOMENTS
) -> List[Dict]:
    """
    Use an LLM to find the top shareable clip moments in a video.

    Args:
        entries: timestamped transcript entries
            [{"text": str, "start": seconds, "duration": seconds}, ...]
        max_moments: how many moments to return (default 3)

    Returns:
        [{"start_sec", "end_sec", "start", "end", "title", "reason"}, ...]

    Raises:
        RuntimeError if the LLM is unavailable or returns nothing usable.
    """
    if not entries:
        raise ValueError("No transcript entries provided")

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "langchain-openai is not installed; clip detection needs it"
        ) from exc

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set; clip detection needs it")

    duration = max(
        float(e.get("start", 0)) + float(e.get("duration", 0)) for e in entries
    )
    transcript_text = _entries_to_prompt_text(entries)

    llm = ChatOpenAI(
        openai_api_key=api_key,
        model_name="gpt-4o-mini",
        temperature=0.3,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    system_prompt = (
        "You are a short-form video editor. Given a timestamped transcript, "
        "pick the moments most likely to perform as standalone short clips: "
        "strong hooks, surprising insights, emotional peaks, quotable lines. "
        "Each moment must be 15-60 seconds long. "
        'Return ONLY valid JSON: {"moments": [{"start_sec": number, '
        '"end_sec": number, "title": string, "reason": string}]}. '
        "start_sec/end_sec are seconds from the start of the video. "
        "Titles are punchy, under 60 characters, no hashtags."
    )
    human_prompt = (
        f"Video duration is about {duration:.0f} seconds. "
        f"Find the top {max_moments} clip-worthy moments.\n\n"
        f"Transcript:\n{transcript_text}"
    )

    try:
        raw = llm.invoke([("system", system_prompt), ("human", human_prompt)]).content
        data = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"Clip-moment analysis failed: {exc}") from exc

    moments = data.get("moments", data if isinstance(data, list) else [])
    cleaned: List[Dict] = []
    for moment in moments[:max_moments]:
        try:
            start = max(0.0, float(moment.get("start_sec", 0)))
            end = min(float(moment.get("end_sec", start + 30)), duration)
            if end - start < 5:  # too short to be a clip; pad it
                end = min(start + 30, duration)
            if end - start < 5:
                continue
            cleaned.append(
                {
                    "start_sec": round(start, 1),
                    "end_sec": round(end, 1),
                    "start": format_timestamp(start),
                    "end": format_timestamp(end),
                    "title": str(moment.get("title", "Highlight"))[:120],
                    "reason": str(moment.get("reason", ""))[:280],
                }
            )
        except (TypeError, ValueError):
            continue

    if not cleaned:
        raise RuntimeError("The AI did not return any usable clip moments")
    logger.info("detected %d clip moments (video %.0fs)", len(cleaned), duration)
    return cleaned


def cut_clips_from_file(
    video_file: str, moments: List[Dict], output_dir: str
) -> List[str]:
    """
    Cut clip moments from a LOCAL video file using ffmpeg.

    Only use with video files you have the rights to edit (never with
    videos downloaded from YouTube -- that violates YouTube's ToS).

    Returns the list of output file paths.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg is not installed. Install it (e.g. `apt install ffmpeg`) "
            "to enable clip cutting."
        )
    if not os.path.exists(video_file):
        raise FileNotFoundError(f"Video file not found: {video_file}")
    os.makedirs(output_dir, exist_ok=True)

    outputs: List[str] = []
    for i, moment in enumerate(moments):
        out_path = os.path.join(
            output_dir, f"clip_{i + 1}_{int(moment['start_sec'])}s.mp4"
        )
        cmd = [
            ffmpeg, "-y",
            "-ss", str(moment["start_sec"]),
            "-to", str(moment["end_sec"]),
            "-i", video_file,
            "-c", "copy",
            out_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        outputs.append(out_path)
    return outputs

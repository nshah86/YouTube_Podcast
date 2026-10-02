#!/usr/bin/env python3
"""
VideoTranscript Pro MCP server.

Exposes transcript / summary / podcast / clip-moment tools to MCP clients
(Claude Desktop, etc.). This server is a thin client over the VideoTranscript
Pro HTTP API: set VTP_API_TOKEN to one of your API tokens (generated on the
/account page) and every call is authenticated, plan-gated, and counted
against your API quota server-side.

Run:
    VTP_API_TOKEN=... VTP_API_BASE_URL=https://your-domain python mcp_server.py

Claude Desktop config (~/.claude_desktop_config.json):
    {
      "mcpServers": {
        "videotranscript-pro": {
          "command": "python",
          "args": ["/absolute/path/to/mcp_server.py"],
          "env": {
            "VTP_API_TOKEN": "your-api-token",
            "VTP_API_BASE_URL": "https://your-domain"
          }
        }
      }
    }
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASE = os.environ.get("VTP_API_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
API_TOKEN = os.environ.get("VTP_API_TOKEN", "").strip()


def _extract_video_id(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if qs.get("v"):
        return qs["v"][0]
    if "youtu.be" in (parsed.netloc or ""):
        return parsed.path.lstrip("/").split("/")[0]
    m = re.search(r"/(shorts|embed|live)/([^/?]+)", parsed.path)
    if m:
        return m.group(2)
    raise ValueError("Could not extract a video ID from that URL")


def _api_post(path: str, payload: dict) -> dict:
    """POST to the VideoTranscript Pro API with the configured token."""
    if not API_TOKEN:
        raise RuntimeError(
            "VTP_API_TOKEN is not set. Generate a token on the /account page "
            "and export it before starting this server."
        )
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_BASE + path,
        data=data,
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"API error {exc.code}: {body[:500]}") from exc


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "The 'mcp' package is not installed. Run: pip install mcp",
        file=sys.stderr,
    )
    sys.exit(1)

mcp = FastMCP("videotranscript-pro")


@mcp.tool()
def get_transcript(video_url: str) -> str:
    """Fetch the full transcript of a YouTube video. Free tier: 20 API requests/month."""
    video_id = _extract_video_id(video_url)
    result = _api_post("/api/transcripts", {"ids": [video_id]})
    items = result.get("results", [])
    if not items or not items[0].get("success"):
        detail = items[0].get("error") if items else result.get("error", "unknown error")
        return f"Transcript unavailable: {detail}"
    return items[0]["transcript"]


@mcp.tool()
def summarize_video(video_url: str) -> str:
    """Generate an AI summary (title + 400-600 words) of a YouTube video. Requires Plus plan or higher."""
    result = _api_post("/api/summarize", {"url": video_url})
    if not result.get("success"):
        return f"Summary failed: {result.get('error', 'unknown error')}"
    return f"{result.get('title', '')}\n\n{result.get('summary', '')}"


@mcp.tool()
def generate_podcast_episode(video_url: str, voice: str = "female") -> str:
    """Generate a podcast episode (two-host script + MP3 audio) from a YouTube video. Requires Plus plan or higher. Voice: 'female', 'male', or 'mixed'."""
    result = _api_post("/api/podcast", {"url": video_url, "voice": voice})
    if not result.get("success"):
        return f"Podcast generation failed: {result.get('error', 'unknown error')}"
    return (
        f"Title: {result.get('title', '')}\n\n"
        f"Script:\n{result.get('conversation', '')}\n\n"
        f"Audio: {API_BASE}{result.get('audio_url', '')}"
    )


@mcp.tool()
def find_clip_moments(video_url: str) -> str:
    """Find the top 3 shareable short-clip moments (timestamps + titles) in a YouTube video. Requires Plus plan or higher."""
    result = _api_post("/api/clips", {"url": video_url})
    if not result.get("success"):
        return f"Clip detection failed: {result.get('error', 'unknown error')}"
    lines = [
        f"{m['start']} - {m['end']}: {m['title']}"
        + (f" ({m['reason']})" if m.get("reason") else "")
        for m in result.get("moments", [])
    ]
    return "\n".join(lines) if lines else "No clip moments found."


if __name__ == "__main__":
    mcp.run()

# Deploying VideoTranscript Pro to production

## 1. Prerequisites

- Python 3.10+
- A Supabase project (free tier works)
- A Stripe account (start in **test mode**)
- An OpenAI API key (only needed for AI summaries / podcast scripts)

## 2. Environment variables

Copy `.env.example` to `.env` and fill in every value. Full checklist:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | yes | Long random string (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `APP_ENV` | yes | `production` |
| `APP_BASE_URL` | yes | Public URL, e.g. `https://ytp.example.com` (used for Stripe redirects) |
| `SUPABASE_URL` | yes | From Supabase dashboard |
| `SUPABASE_ANON_KEY` | yes | From Supabase dashboard |
| `SUPABASE_SERVICE_KEY` | yes | Service-role key — **server only**, used by the Stripe webhook |
| `OPENAI_API_KEY` | for AI features | Summaries + podcast scripts |
| `YOUTUBE_API_KEY` | no | Official captions API — only helps for videos you own |
| `TRANSCRIPT_FALLBACK_PROVIDER` | no | Paid transcript fallback; currently `supadata` |
| `TRANSCRIPT_FALLBACK_API_KEY` | no | API key for the fallback provider |
| `VTP_API_TOKEN` | for MCP server | API token from /account (MCP calls your HTTP API) |
| `VTP_API_BASE_URL` | for MCP server | Public API URL, e.g. `https://ytp.example.com` |
| `STRIPE_SECRET_KEY` | yes | `sk_live_...` in production |
| `STRIPE_PUBLISHABLE_KEY` | yes | `pk_live_...` (currently unused server-side, kept for future) |
| `STRIPE_WEBHOOK_SECRET` | yes | From the webhook endpoint created in step 4 (`whsec_...`) |
| `STRIPE_PRICE_PLUS_MONTHLY` | yes | Price ID, e.g. `price_...` |
| `STRIPE_PRICE_PRO_MONTHLY` | yes | Price ID, e.g. `price_...` |

## 3. Database

In the Supabase SQL editor, run the migrations in order:

1. `supabase/migrations/20251129081910_create_core_schema.sql`
2. `supabase/migrations/20261002120000_add_billing.sql` (adds `subscriptions`, `payments`, `user_profiles.stripe_customer_id`)

## 4. Stripe setup

1. In the Stripe Dashboard → **Product catalog**, create two recurring monthly products:
   - **Plus** — $9/mo → copy its Price ID into `STRIPE_PRICE_PLUS_MONTHLY`
   - **Pro** — $29/mo → copy its Price ID into `STRIPE_PRICE_PRO_MONTHLY`
2. **Developers → Webhooks → Add endpoint**: `https://YOUR-DOMAIN/billing/webhook`
   - Subscribe to events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
   - Copy the **signing secret** into `STRIPE_WEBHOOK_SECRET`
3. Test with the Stripe CLI before going live:
   `stripe listen --forward-to localhost:5000/billing/webhook`
   then trigger `checkout.session.completed` from the dashboard.

## 5. Run locally

```bash
pip install -r requirements.txt
python start.py        # or: python app.py
```

## 6. Production run (gunicorn)

```bash
pip install -r requirements.txt
gunicorn "app:app" --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

Podcast audio generation can take a while — the 120s timeout matters.

### Render (recommended, ~$7/mo starter)

1. New → Web Service → connect this repo, branch `main`
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn "app:app" --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
4. Add all env vars from section 2
5. Deploy, then point the Stripe webhook at `https://<your-render-url>/billing/webhook`

### Railway

Same as Render: build `pip install -r requirements.txt`, start command above,
add env vars, generate a public domain, configure the Stripe webhook URL.

### Any VPS (cheapest long-term, ~$4–6/mo)

```bash
# with a process manager, e.g. systemd
gunicorn "app:app" --bind 127.0.0.1:8000 --workers 2 --timeout 120
# put Caddy/Nginx in front for TLS: caddy reverse-proxy --from ytp.example.com --to 127.0.0.1:8000
```

## 7. Post-deploy smoke tests

- `GET /healthz` → `{"status":"ok"}`
- Open `/` and `/pricing` in a browser (templates render, no 500s)
- Sign up, extract a transcript (free, no plan needed)
- Try `/generate-summary` on a free account → expect **402** with an upgrade message
- In Stripe **test mode**, buy Plus → webhook fires → `/account` shows plan `plus`
- Stripe Dashboard → Billing → cancel the test subscription → plan drops back to `free`

## 8. Monitoring (minimal)

- Uptime: add the `/healthz` URL to any uptime monitor (Better Stack free, UptimeRobot free).
- Errors: optional but recommended — `pip install sentry-sdk` and init it in `app.py`
  with `SENTRY_DSN` from your Sentry project.
- Logs: `LOG_LEVEL=INFO` (default); set `WERKZEUG_LOG_LEVEL=WARNING` to cut noise.

## 9. Transcript fallback chain

`src/youtube_podcast/utils/youtube_utils.py` tries sources in order and logs
which one succeeded (`transcript acquired: video_id=... source=...`):

1. **Official YouTube Data API v3 captions** — needs `YOUTUBE_API_KEY`; only
   works for videos you own. Fails fast otherwise.
2. **youtube-transcript-api** (community extractor) — English preferred, then
   any available track. This breaks periodically when YouTube changes things;
   keep the package updated (`pip install -U youtube-transcript-api`).
3. **Paid fallback** — set `TRANSCRIPT_FALLBACK_PROVIDER=supadata` and
   `TRANSCRIPT_FALLBACK_API_KEY` for a hosted fallback when the extractor is
   blocked (Supadata free tier covers light use).

When every source fails the API returns an honest
`"Transcripts are unavailable for this video right now."` — never a fabricated
transcript.

## 10. API quotas & new endpoints

- Monthly API **request** quotas (separate from AI token quotas):
  free 20 · plus 2,000 · pro 50,000. Enforced by `requires_api_quota`
  (`429` + `upgrade_url` when exhausted).
- Every API response carries `X-Quota-Limit`, `X-Quota-Remaining`,
  `X-Quota-Plan` headers.
- New Plus+ endpoints: `POST /api/summarize`, `POST /api/podcast`
  (`voice`: female/male/mixed), `POST /api/clips` (top 3 clip moments).
  AI endpoints consume 10 AI tokens each on top of the request quota.
- Web UI: `/generate-clips` (Plus+) powers the "Clip moments" card on `/`.

## 11. MCP server (Claude Desktop / agents)

`mcp_server.py` exposes `get_transcript`, `summarize_video`,
`generate_podcast_episode`, `find_clip_moments` as MCP tools. It is a thin
client over your HTTP API, so plan gating and quotas apply automatically.

```bash
pip install -r requirements.txt   # includes `mcp`
VTP_API_TOKEN=<token-from-/account> VTP_API_BASE_URL=https://YOUR-DOMAIN \
  python mcp_server.py
```

Claude Desktop (`~/.claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "videotranscript-pro": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"],
      "env": {
        "VTP_API_TOKEN": "your-api-token",
        "VTP_API_BASE_URL": "https://YOUR-DOMAIN"
      }
    }
  }
}
```

## 12. Clip moments & ffmpeg

`/api/clips` and `/generate-clips` return the top 3 shareable moments with
timestamps + titles (LLM detection only). Cutting video files server-side is
deliberately out of scope — downloading YouTube videos violates YouTube's ToS.
`src/youtube_podcast/utils/clips.py::cut_clips_from_file` cuts moments from a
**local** video file you have rights to, if `ffmpeg` is installed
(`apt install ffmpeg` on a VPS; not available on Render/Railway by default).

## 13. Known limitations / follow-ups

- Playlist/channel endpoints need a YouTube Data API v3 key (currently return a placeholder message).
- Server-side Supabase writes (billing, tokens) use the service-role key; the older
  anon-key code paths assume permissive RLS. If you tighten RLS, pass the user's JWT
  via `supabase.auth.set_session()` or route all writes through the service key.
- `output/` holds generated MP3s on local disk — on Render/Railway use a persistent
  volume or move to Supabase Storage before scaling.

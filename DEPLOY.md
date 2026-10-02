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

## 9. Known limitations / follow-ups

- Playlist/channel endpoints need a YouTube Data API v3 key (currently return a placeholder message).
- Server-side Supabase writes (billing, tokens) use the service-role key; the older
  anon-key code paths assume permissive RLS. If you tighten RLS, pass the user's JWT
  via `supabase.auth.set_session()` or route all writes through the service key.
- `output/` holds generated MP3s on local disk — on Render/Railway use a persistent
  volume or move to Supabase Storage before scaling.

# oneshot-date 💌

A single, dedicated "will you go on a date with me?" web page. The recipient
(name set in `.env`) taps through a few playful multi-select steps —
**entertainment → eating → drinking → when** — and finally answers **yes / no**.

When she answers:

1. her full set of choices is stored in **Postgres**, and
2. you get an **instant Telegram message** with everything she picked.

There's a password-protected **`/admin`** dashboard to review every response,
jot private notes, and delete test entries.

## Features

- Multi-step, multi-select wizard with a free-text "Something else…" option.
- A cheeky **"No" button that runs away** from the cursor 🙈 (saying no is *technically* possible).
- **Telegram** ping the moment she answers, and again with the full plan.
- **"View your plan"** for a returning visitor — backed by the server via an opaque token, so Postgres stays the source of truth.
- **Reusable for a different girl**: change `GIRL_NAME` and redeploy; each response remembers the girl it was for.
- **Admin**: per-response private **notes** + **delete**.
- Tuned for **mobile / iOS** (safe-area insets, `dvh`, no focus-zoom, HTTPS-ready).

## Stack

FastAPI · Jinja2 · SQLAlchemy 2 + Alembic · PostgreSQL 16 · Telegram Bot API.
One small Python app, packaged with Docker Compose.

## Routes

| Path | What |
|------|------|
| `GET /` | The invite wizard (this is the link you send her) |
| `POST /api/answer` | Records yes/no, sends Telegram #1 |
| `POST /api/plan` | Saves her picks, sends Telegram #2 |
| `GET /api/response/{token}` | Re-opens a saved plan for a returning visitor |
| `GET /admin` · `/admin/login` · `/admin/logout` | Dashboard + auth |
| `POST /admin/responses/{id}/note` | Save an admin note on a response |
| `POST /admin/responses/{id}/delete` | Delete a response |
| `GET /healthz` | Health check |

## Run it (Docker — recommended)

```bash
cp .env.example .env
#  …edit .env: set GIRL_NAME, ADMIN_PASSWORD, SESSION_SECRET, and (optionally) Telegram
docker compose up -d --build
```

- Page:  http://localhost:8000/
- Admin: http://localhost:8000/admin

The `web` container runs `alembic upgrade head` on boot (creates the tables) and
seeds the admin user from `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

## Run it (local, without Docker)

Needs Python 3.11+ and a running Postgres.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # point DATABASE_URL at your Postgres
alembic upgrade head            # create tables
uvicorn app.main:app --reload   # seeds admin on startup
```

## Configuration (`.env`)

| Variable | Purpose |
|----------|---------|
| `GIRL_NAME` | Who the page is for (shown everywhere; never hardcoded) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Provision the Postgres container (and feed `DATABASE_URL`) |
| `DATABASE_URL` | Auto-set by compose; only set it yourself when running without Docker |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Notifications (blank → storage still works, send is skipped) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Seed the `/admin` login on first boot |
| `SESSION_SECRET` | Signs admin session cookies (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `SITE_ADDRESS` | Public domain for HTTPS in production (see Deployment) |

## Customizing the questions

The option steps live in **`app/steps.py`** — edit the titles and option lists
there. The "When works for you?" chips are in `app/templates/invite.html`.

## Telegram setup

1. Message **@BotFather**, `/newbot`, copy the token → `TELEGRAM_BOT_TOKEN`.
2. Open a chat with your new bot and send it any message.
3. Message **@userinfobot** to get your numeric chat id → `TELEGRAM_CHAT_ID`.

If these are blank the app still works — answers are stored, the Telegram send is
just skipped (logged as a warning).

## Deployment (VPS, with HTTPS)

The base `docker compose up -d --build` is the whole app. For a public server with
automatic HTTPS, use the **production overlay** (adds [Caddy](https://caddyserver.com/)
in front and keeps the app bound to localhost):

```bash
# .env: set SITE_ADDRESS=your-name.duckdns.org  (a free DuckDNS subdomain works great)
sudo ufw allow 80 && sudo ufw allow 443
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Caddy fetches a Let's Encrypt certificate for `SITE_ADDRESS` automatically.

**CI/CD:** `.github/workflows/ci-cd.yml` builds + boot-tests the stack on every
push, and on `main` (after CI passes) SSHes into the VPS and runs
`git pull && docker compose … up -d --build`. Set repo secrets `VPS_HOST`,
`VPS_USER`, `VPS_SSH_KEY` (+ optional `SSH_PORT`, `VPS_APP_DIR`) to enable auto-deploy.

**Back up the responses:** `docker compose exec db pg_dump -U <user> <db> > backup.sql`

## Reuse for a different girl

Change `GIRL_NAME` in `.env` and redeploy — the page rebrands. The previous girl's
cached "view your plan" won't show (the name no longer matches), and every stored
response keeps the `girl_name` it was for.

---

Working on the code? See **[CLAUDE.md](CLAUDE.md)** for architecture, conventions,
and gotchas.

# oneshot-simping 💌

A single, dedicated "will you go out with me?" web page. The recipient
(name set in `.env`) taps through a few playful multi-select steps —
**entertainment → eating → drinking → when** — and finally answers **yes / no**.

When she answers:
1. her full set of choices is stored in **Postgres**, and
2. you get an **instant Telegram message** with everything she picked.

There's also a password-protected **`/admin`** page that lists every response.

## Stack
FastAPI · Jinja2 · SQLAlchemy + Alembic · Postgres · Telegram Bot API. One small
Python app, packaged with Docker Compose for easy hosting.

## Routes
| Path | What |
|------|------|
| `/` | The invite wizard (this is the link you send her) |
| `/api/respond` | POST endpoint the wizard submits to (stores + notifies) |
| `/admin` | Responses dashboard (login required) |
| `/admin/login`, `/admin/logout` | Admin auth |
| `/healthz` | Health check |

---

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

---

## Admin credentials
The admin user is seeded from the `.env` values on startup (idempotent — only
created if it doesn't already exist). To (re)seed manually:
```bash
python -m app.seed
```
To change the password later: delete the row in `admin_users` and restart, or
update the hash directly.

## Telegram setup
1. Message **@BotFather**, `/newbot`, copy the token → `TELEGRAM_BOT_TOKEN`.
2. Open a chat with your new bot and send it any message.
3. Message **@userinfobot** to get your numeric chat id → `TELEGRAM_CHAT_ID`.

If these are blank the app still works — answers are stored, the Telegram send is
just skipped (logged as a warning).

## Customizing the questions
Everything she picks from lives in **`app/steps.py`** — edit the step titles and
the option lists there. The girl's name is **never hardcoded**; it comes from
`GIRL_NAME` in `.env`.

## Deploying to a VPS
`docker compose up -d --build` is the whole deploy. Put nginx (or Caddy) in front
for HTTPS and proxy to `127.0.0.1:8000`. If you'd rather use a managed/existing
Postgres instead of the bundled container, drop the `db` service and point
`DATABASE_URL` at it. Ping me when you set up the VPS and I'll help wire this up.

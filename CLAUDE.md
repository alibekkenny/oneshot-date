# CLAUDE.md

Guidance for working in this repo. Read this first.

## What this is

**oneshot-date** (a.k.a. "oneshot-simping") — a single-page, multi-step
"will you go on a date with me?" web invite, dedicated to **one girl at a time**.
She taps through playful multi-select steps (**entertainment → eating → drinking
→ when**) and finally answers **yes / no**. On her answer:

1. her choices are stored in **Postgres**, and
2. the owner gets an **instant Telegram message** with everything she picked.

A password-protected **`/admin`** page lists every response. The girl's name is
**never hardcoded** — it comes from `GIRL_NAME` in `.env`. The app is built to be
**reused for a different girl later**: change `GIRL_NAME`, redeploy, and the page
rebrands; each stored response remembers the `girl_name` it was for.

## Stack

FastAPI · Jinja2 · SQLAlchemy 2 + Alembic · PostgreSQL 16 · Telegram Bot API.
Python 3.12, packaged with Docker Compose.

## How it works (request flow)

1. `GET /` → the `invite.html` wizard. Option steps come from `app/steps.py`; the
   "when" step's chips are inline in the template.
2. `POST /api/answer {answer}` → creates a `responses` row with a random
   `public_token`, sends Telegram message #1, returns `{id, token}`.
3. `POST /api/plan {id, picks…}` → saves her choices on that row, sends Telegram
   message #2, returns `{id, token}`.
4. The browser keeps **only** `{token, girl_name}` in `localStorage`. A returning
   visitor re-opens her plan via `GET /api/response/{token}` (Postgres is the
   source of truth). If the stored `girl_name` ≠ the current `GIRL_NAME` (page was
   repurposed), the cache is cleared and the "view your plan" button stays hidden.
5. `/admin` (session login) lists responses, with a per-row **note** editor
   (`POST /admin/responses/{id}/note`) and **delete** (`POST /admin/responses/{id}/delete`).
6. `/healthz` → health check. All HTML responses get `Cache-Control: no-cache`
   (middleware) so a new build's versioned assets always load.

## Key files

- `app/main.py` — all routes, the two-step submit API, admin, the no-cache middleware.
- `app/models.py` — `Response` (incl. `public_token`, `girl_name`, JSONB picks, `note`) and `AdminUser`.
- `app/config.py` — settings from env (`GIRL_NAME`, `DATABASE_URL`, Telegram, admin creds, `SESSION_SECRET`).
- `app/steps.py` — **edit here to change the question options.** The "when" chips live in `app/templates/invite.html`.
- `app/static/wizard.js` — wizard flow, the localStorage token logic, the runaway "No" button.
- `app/static/styles.css` — all styling (cache-busted via `?v=N`).
- `app/templates/` — `base.html`, `invite.html`, `admin.html`, `admin_login.html`.
- `app/seed.py` — seeds the admin user from env on startup (idempotent).
- `alembic/versions/` — `0001` initial schema, `0002` adds `public_token`.

## Run locally

```bash
cp .env.example .env       # set GIRL_NAME, ADMIN_PASSWORD, SESSION_SECRET, (optional) Telegram
docker compose up -d --build   # runs `alembic upgrade head` then uvicorn; page on http://localhost:8000
```

## Deployment (production)

- VPS (Ubuntu), app cloned to `/opt/oneshot-date`, owned by the `deploy` user (in the `docker` group).
- Prod overlay adds **Caddy** for automatic HTTPS; `web` binds to `127.0.0.1` only, Caddy fronts 80/443:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
  ```
- Domain via **DuckDNS** (free subdomain) set in `.env` as `SITE_ADDRESS`; Caddy auto-issues a Let's Encrypt cert.
- **CI/CD** (`.github/workflows/ci-cd.yml`): on push, CI builds + boot-tests the stack; on `main` (after CI passes)
  the deploy job SSHes into the VPS and runs `git pull && docker compose … up -d --build`.
  Requires GitHub secrets `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY` (+ optional `SSH_PORT`, `VPS_APP_DIR`).

## Reuse for a different girl

- Change `GIRL_NAME` in `.env` and redeploy → the page rebrands. The previous girl's
  cached "view your plan" won't show (girl_name mismatch auto-clears it).
- Every response already stores its `girl_name`, so past answers stay attributable across changes.

## Conventions

- **Code changes go on a feature branch**, get tested, then merge to `main` — do not commit code directly to `main`.
- **Commit messages**: one short Conventional Commits line (`type(scope): subject`) + the
  `Co-Authored-By: Claude …` trailer. No multi-paragraph bodies.
- **Secrets are never committed**: `.env` / `.env.*` are gitignored (except `.env.example`);
  `.dockerignore` keeps them out of the image; config reaches containers via compose `environment:`.
- **Asset cache-busting**: when you change `styles.css` or `wizard.js`, bump the `?v=N` query in
  `base.html` / `invite.html`.
- **Verify before claiming done**: check changes by actually running the app (an isolated Docker
  stack + a real browser), not by assertion.

## Gotchas

- `position: fixed` resolves against the nearest *transformed* ancestor. The wizard panels animate
  (leaving a transform), so the runaway "No" button re-parents itself to `<body>` to stay
  viewport-relative — otherwise it flies off-screen.
- Postgres applies `POSTGRES_USER` / `POSTGRES_PASSWORD` **only on first init** of the `pgdata`
  volume. Changing them later needs `down -v` (wipes data) or `ALTER USER` inside Postgres.
- Data lives in the `pgdata` Docker volume, not in the project dir. Back up:
  `docker compose exec db pg_dump -U <user> <db> > backup.sql`.

## Ideas / TODO

- **Multi-girl admin**: turn `/admin` into a dashboard that groups all responses by `girl_name`
  (with per-girl stats), so the app can be reused for different people over time. The data already
  carries `girl_name` per row, so this is a presentation change — no migration needed.

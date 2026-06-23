"""FastAPI app: the public wizard, the submit API, and the admin panel."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from . import telegram
from .config import get_settings
from .db import get_db
from .models import AdminUser, Response as DateResponse
from .security import verify_password
from .seed import seed_admin
from .steps import STEPS

logging.basicConfig(level=logging.INFO)
settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_admin()
    yield


app = FastAPI(title=settings.app_title, lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# --------------------------------------------------------------------------- #
# Public wizard
# --------------------------------------------------------------------------- #
class AnswerPayload(BaseModel):
    answer: str  # "yes" | "no"


class PlanPayload(BaseModel):
    id: int | None = None  # the row created by /api/answer
    entertainment: list[str] = Field(default_factory=list)
    eating: list[str] = Field(default_factory=list)
    drinking: list[str] = Field(default_factory=list)
    proposed_when: str | None = None


@app.get("/", response_class=HTMLResponse)
def invite(request: Request):
    return templates.TemplateResponse(
        request,
        "invite.html",
        {
            "girl_name": settings.girl_name,
            "steps": STEPS,
            # +1 for the "when" step that follows the option steps.
            "total_steps": len(STEPS) + 1,
        },
    )


@app.post("/api/answer")
def answer(payload: AnswerPayload, request: Request, db: Session = Depends(get_db)):
    """Step 1: she tapped yes/no. Record it and notify immediately (Telegram #1)."""
    ans = (payload.answer or "").lower()
    if ans not in {"yes", "no"}:
        raise HTTPException(status_code=400, detail="answer must be 'yes' or 'no'")

    row = DateResponse(
        girl_name=settings.girl_name,
        answer=ans,
        entertainment=[],
        eating=[],
        drinking=[],
        user_agent=request.headers.get("user-agent"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    if ans == "yes":
        msg = f"💘 <b>{row.girl_name} said YES!</b> 🎉\nShe's picking the date plan now…"
    else:
        msg = f"🥀 {row.girl_name} said no — it's okay."
    telegram.send_message(msg)

    return {"ok": True, "id": row.id, "token": row.public_token}


@app.post("/api/plan")
def plan(payload: PlanPayload, db: Session = Depends(get_db)):
    """Step 2: she finished the picks. Save the plan and notify again (Telegram #2)."""
    row = db.get(DateResponse, payload.id) if payload.id else None
    if row is None:
        # Fallback if the initial /api/answer id was lost — still capture a "yes".
        row = DateResponse(girl_name=settings.girl_name, answer="yes")
        db.add(row)

    row.entertainment = payload.entertainment
    row.eating = payload.eating
    row.drinking = payload.drinking
    row.proposed_when = payload.proposed_when
    db.commit()
    db.refresh(row)

    telegram.send_message(_format_plan_message(row))
    return {"ok": True, "id": row.id, "token": row.public_token}


@app.get("/api/response/{token}")
def get_response(token: str, db: Session = Depends(get_db)):
    """Returning visitor: render her saved plan from the DB by her opaque token.

    The browser only keeps the token (in localStorage); the answers live here so
    Postgres stays the source of truth.
    """
    row = db.query(DateResponse).filter_by(public_token=token).first()
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return {
        "girl_name": row.girl_name,
        "answer": row.answer,
        "entertainment": row.entertainment or [],
        "eating": row.eating or [],
        "drinking": row.drinking or [],
        "proposed_when": row.proposed_when,
    }


def _format_plan_message(row: DateResponse) -> str:
    def fmt(items: list[str]) -> str:
        return ", ".join(items) if items else "—"

    lines = [
        f"🗓 <b>{row.girl_name}'s date plan</b> 💌",
        "",
        f"🎬 Entertainment: {fmt(row.entertainment)}",
        f"🍝 Eating: {fmt(row.eating)}",
        f"🥤 Drinking: {fmt(row.drinking)}",
    ]
    if row.proposed_when:
        lines.append(f"🗓 When: {row.proposed_when}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Admin panel
# --------------------------------------------------------------------------- #
def _is_admin(request: Request) -> bool:
    return bool(request.session.get("admin"))


@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_form(request: Request):
    if _is_admin(request):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(request, "admin_login.html", {"error": None})


@app.post("/admin/login")
def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(AdminUser).filter_by(username=username).first()
    if user is None or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "admin_login.html",
            {"error": "Wrong username or password."},
            status_code=401,
        )
    request.session["admin"] = user.username
    return RedirectResponse("/admin", status_code=303)


@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if not _is_admin(request):
        return RedirectResponse("/admin/login", status_code=303)

    rows = db.query(DateResponse).order_by(DateResponse.created_at.desc()).all()
    total = len(rows)
    yes = sum(1 for r in rows if r.answer == "yes")
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "rows": rows,
            "total": total,
            "yes": yes,
            "no": total - yes,
            "girl_name": settings.girl_name,
            "admin": request.session.get("admin"),
        },
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

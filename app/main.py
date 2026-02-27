from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.config import get_settings
from app.database import init_db
from app.routers import auth_router, player, admin, background, users, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.images_dir.mkdir(parents=True, exist_ok=True)
    # Optional bootstrap: only create default admin (admin/admin) if explicitly enabled (e.g. local dev).
    # In production leave CREATE_DEFAULT_ADMIN unset or false; create first admin with: python -m app.scripts.create_admin
    from sqlalchemy import select
    from app.database import get_session_factory
    from app.models import User, UserRole
    from app.auth import hash_password
    if settings.create_default_admin:
        session_factory = get_session_factory()
        async with session_factory() as db:
            r = await db.execute(select(User).limit(1))
            if r.scalar_one_or_none() is None:
                admin = User(username="admin", password_hash=hash_password("admin"), role=UserRole.admin)
                db.add(admin)
                await db.commit()
    yield


app = FastAPI(title="NivPro", lifespan=lifespan)

app.include_router(auth_router.router)
app.include_router(player.router)
app.include_router(admin.router)
app.include_router(background.router)
app.include_router(users.router)
app.include_router(settings.router)

# Static and templates
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/")
async def player_page(request: Request):
    return templates.TemplateResponse("player.html", {"request": request})


@app.get("/admin")
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/health")
async def health():
    return {"status": "ok"}

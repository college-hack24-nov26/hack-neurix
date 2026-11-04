"""
HomeCare+ Backend — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from sqlalchemy import text

from app.config.database import SessionLocal, close_database, ping_database
from app.config.settings import settings
from app.routes import (
    auth, symptoms, diseases, chat, health,
    records, hospitals, insurance, analysis, user, telemedicine, laboratories, history
)


async def _auto_seed_if_empty() -> None:
    """Fresh database -> load the disease library, hospitals and doctors."""
    from app.seeding import seed_all
    async with SessionLocal() as session:
        organ_count = (await session.execute(text("SELECT count(*) FROM organ_systems"))).scalar_one()
        disease_count = (await session.execute(text("SELECT count(*) FROM diseases"))).scalar_one()
    if organ_count and disease_count:
        print(f"Database ready: {disease_count} diseases loaded.")
        return
    print("Database empty — running seeder...")
    async with SessionLocal() as session:          # fresh session: no transaction begun yet
        async with session.begin():                # seed_all takes a Postgres advisory lock, so
            counts = await seed_all(session)       # parallel workers cannot double-seed
    print(f"Seeded: {counts}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify PostgreSQL connection, auto-seed if empty
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    if await ping_database():
        print("Connected to PostgreSQL.")
        try:
            await _auto_seed_if_empty()
        except Exception as e:
            print(
                f"Startup seeding skipped: {e}\n"
                "  -> Have you run the migrations?  `alembic upgrade head`"
            )
    else:
        print(
            "WARNING: Could not connect to PostgreSQL. "
            "Check DATABASE_URL and that the database is running."
        )

    print("HomeCare+ backend started successfully.")
    yield

    await close_database()
    print("HomeCare+ backend shutting down.")


app = FastAPI(
    title="HomeCare+ API",
    description="AI-Powered Digital Healthcare Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Static files ───────────────────────────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Routers ────────────────────────────────────────────────────────────────────
API = "/api"
app.include_router(auth.router,      prefix=f"{API}/auth",      tags=["Authentication"])
app.include_router(user.router,      prefix=f"{API}/auth",      tags=["User Profile"])
app.include_router(symptoms.router,  prefix=f"{API}/symptoms",  tags=["Symptom Checker"])
app.include_router(diseases.router,  prefix=f"{API}/diseases",  tags=["Disease Library"])
app.include_router(chat.router,      prefix=f"{API}/chat",      tags=["AI Chat"])
app.include_router(health.router,    prefix=f"{API}/health",    tags=["Health Metrics"])
app.include_router(records.router,   prefix=f"{API}/records",   tags=["Health Records"])
app.include_router(hospitals.router, prefix=f"{API}/hospitals", tags=["Hospitals"])
app.include_router(insurance.router, prefix=f"{API}/insurance", tags=["Insurance"])
app.include_router(analysis.router,      prefix=f"{API}/analysis",      tags=["AI Analysis"])
app.include_router(telemedicine.router,  prefix=f"{API}/telemedicine",  tags=["Telemedicine"])
app.include_router(laboratories.router,  prefix=f"{API}/laboratories",  tags=["Laboratory"])
app.include_router(history.router,       prefix=f"{API}/history",       tags=["User History"])


@app.get("/api/health-check", tags=["System"])
async def health_check():
    from app.services.ai_service import AIService
    db_ok = await ping_database()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "HomeCare+ API",
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
        "ai_chat_configured": AIService.is_configured(),
        "ai_vision_configured": AIService.is_vision_configured(),
    }

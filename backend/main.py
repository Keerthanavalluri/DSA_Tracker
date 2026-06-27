from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

from backend.database import init_db
from backend.routers import auth, platforms, analytics, ai, study, study_plan

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize database tables."""
    await init_db()
    print("[OK] Database initialized")
    yield
    print("[BYE] Server shutting down")


app = FastAPI(
    title="DSAtracker API",
    description="Competitive programming performance tracker with AI coaching",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(platforms.router)
app.include_router(analytics.router)
app.include_router(ai.router)
app.include_router(study.router)
app.include_router(study_plan.router)


@app.get("/")
async def root():
    return {
        "name": "DSAtracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.routes import events, experiments, incidents, memory, remediation, system, hypotheses

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="IncidentForge API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    # Support the two standard local development origins. Production origin
    # policy remains an explicit deployment concern rather than a wildcard.
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(experiments.router)
app.include_router(remediation.router)
app.include_router(memory.router)
app.include_router(system.router)
app.include_router(events.router)
app.include_router(hypotheses.router)

@app.get("/api/health")
async def health_check():
    from apps.api.persistence.repository import get_repository

    persistence = await get_repository().health_status()
    return {
        "status": "ok",
        "reasoning_mode": "live_model" if settings.FEATHERLESS_API_KEY else "deterministic_demo",
        "featherless_configured": bool(settings.FEATHERLESS_API_KEY),
        "simulation_only": True,
        **persistence,
    }

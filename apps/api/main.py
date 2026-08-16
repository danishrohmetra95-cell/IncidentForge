from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.config import settings
from apps.api.routes import (
    events,
    experiments,
    hypotheses,
    incidents,
    memory,
    remediation,
    system,
    applications
)

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
app.include_router(applications.router)

@app.get("/api/health")
async def health_check():
    from apps.api.persistence.repository import get_repository
    from apps.api.services import get_gateway
    from apps.api.config import settings

    gateway = get_gateway()
    persistence = await get_repository().health_status()
    
    # Check live provider reachability if configured
    provider_available = await gateway.health_check() if gateway.is_configured else False
    
    return {
        "status": "ok",
        "reasoning_mode": "live_model" if provider_available else "deterministic_demo",
        "live_reasoning_configured": gateway.is_configured,
        "active_provider": gateway.active_provider_name if gateway.is_configured and provider_available else None,
        "deterministic_fallback_available": settings.DEMO_MODE,
        "provider_availability": provider_available,
        "simulation_only": True,
        **persistence,
    }

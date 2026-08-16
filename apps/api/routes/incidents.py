"""Incident API routes."""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from packages.contracts.domain import (
    Incident,
    InvestigationState,
    Severity,
    new_id,
)
from apps.api.persistence.repository import get_repository
from packages.simulator.scenarios import load_scenario, list_scenarios, create_twin_from_scenario

logger = logging.getLogger("incidentforge.api")

router = APIRouter(prefix="/api", tags=["incidents"])



# ── Request / Response schemas ───────────────────────────────────

class CreateIncidentRequest(BaseModel):
    title: str
    description: str
    severity: Severity = Severity.SEV_2
    service: str = "checkout-service"
    scenario_id: str | None = None


class IncidentResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    service: str
    status: str
    created_at: str
    resolved_at: str | None = None
    scenario_id: str | None = None
    symptoms: list = Field(default_factory=list)
    hypotheses: list = Field(default_factory=list)
    evidence_count: int = 0
    experiment_count: int = 0
    timeline: list = Field(default_factory=list)


# ── Routes ───────────────────────────────────────────────────────

@router.get("/scenarios")
async def get_scenarios():
    """List available incident scenarios."""
    return list_scenarios()


@router.post("/incidents")
async def create_incident(req: CreateIncidentRequest):
    """Create a new incident."""
    scenario_data = {}
    if req.scenario_id:
        try:
            scenario_data = load_scenario(req.scenario_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unknown scenario: {req.scenario_id}")

    incident = Incident(
        title=req.title,
        description=req.description,
        severity=req.severity,
        service=req.service,
        scenario_id=req.scenario_id,
    )
    repo = get_repository()
    await repo.save_incident(incident)

    return {"id": incident.id, "status": incident.status.value}


@router.get("/incidents")
async def list_incidents():
    """List all incidents."""
    repo = get_repository()
    results = []
    for inc in await repo.list_incidents():
        ctx = repo._contexts.get(inc.id)
        results.append({
            "id": inc.id,
            "title": inc.title,
            "severity": inc.severity.value,
            "service": inc.service,
            "status": inc.status.value,
            "created_at": inc.created_at.isoformat(),
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            "reasoning_mode": inc.reasoning_mode,
            "evidence_count": len(ctx.evidence) if ctx else 0,
            "hypothesis_count": len(ctx.hypotheses) if ctx else 0,
        })
    return results


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get full incident details including investigation state."""
    repo = get_repository()
    inc = await repo.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    ctx = repo._contexts.get(incident_id)

    response = {
        "id": inc.id,
        "title": inc.title,
        "description": inc.description,
        "severity": inc.severity.value,
        "service": inc.service,
        "status": inc.status.value,
        "created_at": inc.created_at.isoformat(),
        "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
        "scenario_id": inc.scenario_id,
        "reasoning_mode": inc.reasoning_mode,
        "symptoms": [s.model_dump() for s in inc.symptoms],
    }

    if ctx:
        response["evidence"] = [e.model_dump() for e in ctx.evidence]
        response["hypotheses"] = [
            {
                "id": h.id,
                "statement": h.statement,
                "status": h.status.value,
                "score": h.score,
                "predictions": [p.model_dump() for p in h.predictions],
                "supporting_evidence": h.supporting_evidence,
                "contradicting_evidence": h.contradicting_evidence,
            }
            for h in ctx.hypotheses
        ]
        response["critiques"] = [
            {
                "hypothesis_id": c.hypothesis_id,
                "objections": c.objections,
                "assumptions": c.assumptions,
                "alternatives": c.alternatives,
                "falsification_criteria": c.falsification_criteria,
                "recommended_experiment": c.recommended_experiment,
            }
            for c in ctx.critiques
        ]
        response["experiments"] = [
            {
                "id": exp.id,
                "target_hypothesis": exp.target_hypothesis,
                "intervention": exp.intervention.model_dump(),
                "status": exp.status,
                "expected_conditions": [ec.model_dump() for ec in exp.expected_conditions],
                "observation_window_seconds": exp.observation_window_seconds,
                "baseline": exp.baseline,
            }
            for exp in ctx.experiments
        ]
        response["observations"] = [
            {
                "experiment_id": obs.experiment_id,
                "baseline": obs.baseline.model_dump(),
                "post_intervention": obs.post_intervention.model_dump(),
                "duration_seconds": obs.duration_seconds,
            }
            for obs in ctx.observations
        ]
        response["verifications"] = [
            {
                "experiment_id": v.experiment_id,
                "outcome": v.outcome.value,
                "conditions": [c.model_dump() for c in v.conditions],
                "passed_count": v.passed_count,
                "failed_count": v.failed_count,
                "explanation": v.explanation,
            }
            for v in ctx.verifications
        ]
        if ctx.remediation:
            response["remediation"] = {
                "id": ctx.remediation.id,
                "type": ctx.remediation.type.value,
                "title": ctx.remediation.title,
                "description": ctx.remediation.description,
                "diff": ctx.remediation.diff,
                "config_change": ctx.remediation.config_change,
                "validation_status": ctx.remediation.validation_status,
                "validation_detail": ctx.remediation.validation_detail,
            }
        response["timeline"] = [
            {
                "id": t.id,
                "event_type": t.event_type,
                "timestamp": t.timestamp.isoformat(),
                "title": t.title,
                "description": t.description,
                "data": t.data,
                "state": t.state.value if t.state else None,
            }
            for t in ctx.timeline
        ]

    return response


@router.post("/incidents/{incident_id}/start")
async def start_investigation(incident_id: str, background_tasks: BackgroundTasks):
    """Trigger autonomous investigation for an incident."""
    repo = get_repository()
    inc = await repo.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    if inc.status != InvestigationState.CREATED:
        raise HTTPException(
            status_code=400,
            detail=f"Investigation already in progress (status: {inc.status.value})",
        )

    background_tasks.add_task(_run_investigation, incident_id)
    return {"status": "investigation_started", "incident_id": incident_id}


@router.post("/incidents/demo")
async def create_demo_incident(background_tasks: BackgroundTasks, scenario_id: str = "incident-001-db-pool"):
    """Create and auto-start the primary demo incident."""
    scenario_data = load_scenario(scenario_id)

    incident = Incident(
        title=scenario_data["title"],
        description=scenario_data["description"],
        severity=Severity(scenario_data["severity"]),
        service=scenario_data["service"],
        scenario_id=scenario_data["id"],
    )
    repo = get_repository()
    await repo.save_incident(incident)

    background_tasks.add_task(_run_investigation, incident.id)

    return {
        "id": incident.id,
        "status": "investigation_started",
        "title": incident.title,
    }


@router.get("/incidents/{incident_id}/timeline")
async def get_timeline(incident_id: str):
    repo = get_repository()
    if not await repo.get_incident(incident_id):
        raise HTTPException(status_code=404, detail="Not found")
    ctx = repo._contexts.get(incident_id)
    if not ctx:
        return []
    return [
        {
            "id": t.id,
            "event_type": t.event_type,
            "timestamp": t.timestamp.isoformat(),
            "title": t.title,
            "description": t.description,
            "data": t.data,
            "state": t.state.value if t.state else None,
        }
        for t in ctx.timeline
    ]


@router.get("/incidents/{incident_id}/evidence")
async def get_evidence(incident_id: str):
    repo = get_repository()
    if not await repo.get_incident(incident_id):
        raise HTTPException(status_code=404, detail="Not found")
    ctx = repo._contexts.get(incident_id)
    if not ctx:
        return []
    return [e.model_dump() for e in ctx.evidence]


@router.get("/incidents/{incident_id}/hypotheses")
async def get_hypotheses(incident_id: str):
    repo = get_repository()
    if not await repo.get_incident(incident_id):
        raise HTTPException(status_code=404, detail="Not found")
    ctx = repo._contexts.get(incident_id)
    if not ctx:
        return []
    return [
        {
            "id": h.id,
            "statement": h.statement,
            "status": h.status.value,
            "score": h.score,
            "predictions": [p.model_dump() for p in h.predictions],
            "supporting_evidence": h.supporting_evidence,
            "contradicting_evidence": h.contradicting_evidence,
        }
        for h in ctx.hypotheses
    ]


# ── Background investigation runner ─────────────────────────────

async def _run_investigation(incident_id: str) -> None:
    """Run the full investigation lifecycle in the background."""
    from apps.api.services import build_orchestrator, get_gateway

    repo = get_repository()
    incident = await repo.get_incident(incident_id)
    if not incident:
        return
    scenario_data = load_scenario(incident.scenario_id) if incident.scenario_id else {}

    try:
        # Only override reasoning_mode for deterministic incidents, preserve live_model for live apps
        if incident.scenario_id and incident.scenario_id != "incident-004-amazon-demo":
            incident.reasoning_mode = "live_model" if get_gateway().is_configured else "deterministic_demo"
            
        orchestrator, event_bus = await build_orchestrator(incident_id)
        
        initial_ctx = repo._contexts.get(incident_id)
        ctx = await orchestrator.run(incident, scenario_data, initial_context=initial_ctx)
        await repo.save_context(ctx)
    except Exception as exc:
        logger.error("Investigation failed for %s: %s", incident_id, exc, exc_info=True)
        incident.status = InvestigationState.FAILED
        await repo.save_incident(incident)
        # Persist whatever context was accumulated before the failure
        if ctx is not None:
            await repo.save_context(ctx)

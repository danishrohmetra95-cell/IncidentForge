from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from apps.api.persistence.repository import IncidentRepository, get_repository
from packages.observability.connector import ApplicationConnector
from packages.contracts.domain import LiveApplicationObservation, Incident, Evidence, EvidenceType, InvestigationState

router = APIRouter(prefix="/api/applications", tags=["applications"])

class ConnectRequest(BaseModel):
    url: str

class ConnectResponse(BaseModel):
    observation: LiveApplicationObservation

class CreateIncidentResponse(BaseModel):
    incident_id: str

@router.post("/connect", response_model=ConnectResponse)
async def connect_application(
    request: ConnectRequest,
    repository: IncidentRepository = Depends(get_repository)
) -> Any:
    try:
        observation = await ApplicationConnector.observe(request.url)
        await repository.save_live_observation(observation)
        return {"observation": observation}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from packages.orchestration.orchestrator import InvestigationContext

@router.post("/{observation_id}/create-incident", response_model=CreateIncidentResponse)
async def create_incident(
    observation_id: str,
    repository: IncidentRepository = Depends(get_repository)
) -> Any:
    observation = await repository.get_live_observation(observation_id)
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")
        
    status = InvestigationState.RESOLVED if observation.status == "HEALTHY" else InvestigationState.CREATED

    incident = Incident(
        title=f"Application Incident: {observation.application_url}",
        description=f"Live application observation indicates {observation.status.value.lower()} state. HTTP {observation.http_status}, {observation.error_rate * 100:.1f}% errors.",
        severity="SEV_2" if observation.status == "UNAVAILABLE" else "SEV_3",
        service=observation.application_url,
        status=status,
        reasoning_mode="live_model"
    )
    
    ctx = InvestigationContext(incident=incident)
    
    obs_text = f"URL: {observation.application_url}\n"
    obs_text += f"Status: {observation.status}\n"
    obs_text += f"HTTP Status: {observation.http_status}\n"
    obs_text += f"Availability: {observation.availability * 100:.1f}%\n"
    if observation.p95_latency is not None:
        obs_text += f"P95 Latency: {observation.p95_latency:.0f}ms\n"
    obs_text += f"Error Rate: {observation.error_rate * 100:.1f}%\n"
    if observation.tls_valid is not None:
        obs_text += f"TLS Valid: {observation.tls_valid}\n"
        
    evidence = Evidence(
        incident_id=incident.id,
        type=EvidenceType.METRIC,
        source="ApplicationConnector",
        observation=obs_text,
        strength=0.9
    )
    
    ctx.evidence.append(evidence)
    await repository.save_context(ctx)
    
    return {"incident_id": incident.id}

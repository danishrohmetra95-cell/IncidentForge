"""Memory routes — incident memory and similar incident retrieval."""

from fastapi import APIRouter, HTTPException

from apps.api.routes.incidents import _incidents, _investigations
from apps.api.services import get_memory_store
from packages.memory.fingerprint import IncidentFingerprinter

router = APIRouter(prefix="/api", tags=["memory"])


@router.get("/incidents/{incident_id}/memory")
async def get_incident_memory(incident_id: str):
    """Get the stored memory record for a resolved incident."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    record = await get_memory_store().get_by_incident(incident_id)
    if record is None:
        return {"incident_id": incident_id, "memory": None, "message": "No verified memory is available yet."}
    return {"incident_id": incident_id, "memory": record.model_dump(mode="json")}


@router.get("/memory/similar/{incident_id}")
async def get_similar_incidents(incident_id: str):
    """Find similar historical incidents."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    record = await get_memory_store().get_by_incident(incident_id)
    if record is not None:
        fingerprint = record.fingerprint
    else:
        context = _investigations.get(incident_id)
        if context is None:
            return {"incident_id": incident_id, "similar": []}
        fingerprint = IncidentFingerprinter().fingerprint(
            context.incident, context.incident.symptoms, context.evidence
        )
    similar = await get_memory_store().find_similar(fingerprint, limit=5)
    return {
        "incident_id": incident_id,
        "similar": [item.model_dump(mode="json") for item in similar if item.incident_id != incident_id],
    }

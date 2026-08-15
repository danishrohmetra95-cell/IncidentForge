"""Remediation routes."""

from fastapi import APIRouter, HTTPException

from apps.api.routes.incidents import _incidents, _investigations

router = APIRouter(prefix="/api", tags=["remediation"])


@router.get("/incidents/{incident_id}/remediation")
async def get_remediation(incident_id: str):
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    ctx = _investigations.get(incident_id)
    if not ctx or not ctx.remediation:
        return None

    rem = ctx.remediation
    return {
        "id": rem.id,
        "incident_id": rem.incident_id,
        "hypothesis_id": rem.hypothesis_id,
        "type": rem.type.value,
        "title": rem.title,
        "description": rem.description,
        "diff": rem.diff,
        "config_change": rem.config_change,
        "validation_status": rem.validation_status,
        "validation_detail": rem.validation_detail,
    }

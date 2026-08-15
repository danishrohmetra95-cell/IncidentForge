"""SSE event types for the live investigation event system.

All events flow through Server-Sent Events (SSE).
No WebSocket — unidirectional server→client is sufficient.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .domain import InvestigationState, now


class InvestigationEvent(BaseModel):
    """Base event emitted during an investigation."""
    event_type: str
    incident_id: str
    timestamp: datetime = Field(default_factory=now)
    data: dict[str, Any] = Field(default_factory=dict)
    state: InvestigationState | None = None


# Concrete event constructors — keep the event_type string stable
# so frontend consumers can switch on it reliably.

def incident_created(incident_id: str, **data: Any) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="incident.created", incident_id=incident_id, data=data
    )

def triage_started(incident_id: str) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="triage.started", incident_id=incident_id,
        state=InvestigationState.TRIAGING,
    )

def triage_completed(incident_id: str, **data: Any) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="triage.completed", incident_id=incident_id, data=data,
    )

def evidence_found(incident_id: str, evidence_id: str, summary: str) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="evidence.found", incident_id=incident_id,
        state=InvestigationState.EVIDENCE_COLLECTION,
        data={"evidence_id": evidence_id, "summary": summary},
    )

def hypothesis_created(incident_id: str, hypothesis_id: str, statement: str, score: float) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="hypothesis.created", incident_id=incident_id,
        state=InvestigationState.HYPOTHESIS_GENERATION,
        data={"hypothesis_id": hypothesis_id, "statement": statement, "score": score},
    )

def hypothesis_updated(incident_id: str, hypothesis_id: str, status: str, score: float) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="hypothesis.updated", incident_id=incident_id,
        data={"hypothesis_id": hypothesis_id, "status": status, "score": score},
    )

def critic_started(incident_id: str) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="critic.started", incident_id=incident_id,
        state=InvestigationState.HYPOTHESIS_CRITIQUE,
    )

def critic_completed(incident_id: str, **data: Any) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="critic.completed", incident_id=incident_id, data=data,
    )

def experiment_proposed(incident_id: str, experiment_id: str, intervention: str) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="experiment.proposed", incident_id=incident_id,
        state=InvestigationState.EXPERIMENT_DESIGN,
        data={"experiment_id": experiment_id, "intervention": intervention},
    )

def experiment_validated(incident_id: str, experiment_id: str, approved: bool, reason: str = "") -> InvestigationEvent:
    return InvestigationEvent(
        event_type="experiment.validated", incident_id=incident_id,
        state=InvestigationState.EXPERIMENT_VALIDATION,
        data={"experiment_id": experiment_id, "approved": approved, "reason": reason},
    )

def experiment_started(incident_id: str, experiment_id: str) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="experiment.started", incident_id=incident_id,
        state=InvestigationState.EXPERIMENT_EXECUTION,
    )

def experiment_completed(incident_id: str, experiment_id: str, **data: Any) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="experiment.completed", incident_id=incident_id, data=data,
    )

def belief_updated(incident_id: str, updates: dict[str, float]) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="belief.updated", incident_id=incident_id,
        state=InvestigationState.BELIEF_UPDATE,
        data={"scores": updates},
    )

def remediation_generated(incident_id: str, remediation_id: str, title: str) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="remediation.generated", incident_id=incident_id,
        state=InvestigationState.REMEDIATION,
        data={"remediation_id": remediation_id, "title": title},
    )

def remediation_validated(incident_id: str, remediation_id: str, passed: bool) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="remediation.validated", incident_id=incident_id,
        state=InvestigationState.REMEDIATION_VALIDATION,
        data={"remediation_id": remediation_id, "passed": passed},
    )

def incident_resolved(incident_id: str, root_cause: str, confidence: float) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="incident.resolved", incident_id=incident_id,
        state=InvestigationState.RESOLVED,
        data={"root_cause": root_cause, "confidence": confidence},
    )

def investigation_failed(incident_id: str, reason: str) -> InvestigationEvent:
    return InvestigationEvent(
        event_type="investigation.failed", incident_id=incident_id,
        state=InvestigationState.FAILED,
        data={"reason": reason},
    )

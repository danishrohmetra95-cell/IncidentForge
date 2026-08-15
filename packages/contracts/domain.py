"""Canonical typed contracts for IncidentForge.

These models are the boundary between reasoning, deterministic execution, the
API, and persistence. AI output is parsed into agent contracts before any
executable domain object is constructed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str = "if") -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Severity(str, Enum):
    SEV_1 = "SEV_1"
    SEV_2 = "SEV_2"
    SEV_3 = "SEV_3"
    SEV_4 = "SEV_4"


class InvestigationState(str, Enum):
    CREATED = "CREATED"
    INGESTING = "INGESTING"
    TRIAGING = "TRIAGING"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    HYPOTHESIS_GENERATION = "HYPOTHESIS_GENERATION"
    HYPOTHESIS_CRITIQUE = "HYPOTHESIS_CRITIQUE"
    EXPERIMENT_DESIGN = "EXPERIMENT_DESIGN"
    EXPERIMENT_VALIDATION = "EXPERIMENT_VALIDATION"
    EXPERIMENT_EXECUTION = "EXPERIMENT_EXECUTION"
    OBSERVATION = "OBSERVATION"
    BELIEF_UPDATE = "BELIEF_UPDATE"
    REMEDIATION = "REMEDIATION"
    REMEDIATION_VALIDATION = "REMEDIATION_VALIDATION"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class EvidenceType(str, Enum):
    LOG = "LOG"
    METRIC = "METRIC"
    TRACE = "TRACE"
    CODE = "CODE"
    COMMIT = "COMMIT"
    CONFIG = "CONFIG"
    DEPLOYMENT = "DEPLOYMENT"
    HISTORICAL_INCIDENT = "HISTORICAL_INCIDENT"
    SIMULATION_RESULT = "SIMULATION_RESULT"


class MetricDirection(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"


class HypothesisStatus(str, Enum):
    PROPOSED = "PROPOSED"
    TESTING = "TESTING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    WEAKENED = "WEAKENED"


class VerificationOutcome(str, Enum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class RemediationType(str, Enum):
    CODE_PATCH = "CODE_PATCH"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    ROLLBACK = "ROLLBACK"
    FEATURE_FLAG = "FEATURE_FLAG"
    RESOURCE_ACTION = "RESOURCE_ACTION"


class ModelRole(str, Enum):
    FAST_REASONING = "FAST_REASONING"
    DEEP_REASONING = "DEEP_REASONING"
    SYNTHESIS = "SYNTHESIS"


class Symptom(DomainModel):
    name: str
    metric: str
    direction: MetricDirection
    observed_value: float | None = None
    normal_range: str | None = None

    @property
    def description(self) -> str:
        value = "unknown" if self.observed_value is None else str(self.observed_value)
        return f"{self.name}: {self.metric} {self.direction.value} ({value})"


class Incident(DomainModel):
    id: str = Field(default_factory=lambda: new_id("inc"))
    title: str
    description: str
    severity: Severity
    service: str
    status: InvestigationState = InvestigationState.CREATED
    created_at: datetime = Field(default_factory=now)
    resolved_at: datetime | None = None
    scenario_id: str | None = None
    symptoms: list[Symptom] = Field(default_factory=list)
    reasoning_mode: str = "live_model"


class Evidence(DomainModel):
    id: str = Field(default_factory=lambda: new_id("ev"))
    incident_id: str
    type: EvidenceType
    source: str
    observation: str
    timestamp: datetime = Field(default_factory=now)
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    supports_hypotheses: list[str] = Field(default_factory=list)
    contradicts_hypotheses: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Prediction(DomainModel):
    metric: str
    direction: MetricDirection
    threshold_percentage: float = Field(gt=0.0, le=1000.0)
    description: str = ""


class Hypothesis(DomainModel):
    id: str = Field(default_factory=lambda: new_id("hyp"))
    incident_id: str
    statement: str
    score: float = Field(ge=0.0, le=1.0)
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    predictions: list[Prediction] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)


class Critique(DomainModel):
    id: str = Field(default_factory=lambda: new_id("crit"))
    hypothesis_id: str
    objections: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    evidence_weaknesses: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    falsification_criteria: list[str] = Field(default_factory=list)
    recommended_experiment: str


class InterventionSpec(DomainModel):
    type: str = Field(min_length=1)
    target: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ExperimentControls(DomainModel):
    request_rate: float | None = Field(default=None, gt=0)
    application_version: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class MetricExpectation(DomainModel):
    metric: str
    direction: MetricDirection
    threshold_percentage: float = Field(gt=0.0, le=1000.0)
    baseline_value: float | None = None


class Experiment(DomainModel):
    id: str = Field(default_factory=lambda: new_id("exp"))
    incident_id: str
    target_hypothesis: str
    intervention: InterventionSpec
    controls: ExperimentControls = Field(default_factory=ExperimentControls)
    expected_conditions: list[MetricExpectation] = Field(min_length=1)
    observation_window_seconds: int = Field(default=10, ge=1, le=300)
    failure_conditions: list[str] = Field(default_factory=list)
    status: str = "proposed"
    baseline: dict[str, float] = Field(default_factory=dict)


class TelemetrySnapshot(DomainModel):
    request_rate: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    error_rate: float
    db_connections: float
    db_utilization: float
    cache_hit_rate: float
    cpu: float
    memory: float
    queue_depth: float


class Observation(DomainModel):
    id: str = Field(default_factory=lambda: new_id("obs"))
    experiment_id: str
    baseline: TelemetrySnapshot
    post_intervention: TelemetrySnapshot
    duration_seconds: float
    raw_snapshots: list[TelemetrySnapshot] = Field(default_factory=list)


class ConditionResult(DomainModel):
    metric: str
    expected: str
    observed_value: float
    baseline_value: float
    passed: bool
    detail: str


class VerificationResult(DomainModel):
    id: str = Field(default_factory=lambda: new_id("vrf"))
    experiment_id: str
    outcome: VerificationOutcome
    conditions: list[ConditionResult]
    passed_count: int
    failed_count: int
    explanation: str


class Remediation(DomainModel):
    id: str = Field(default_factory=lambda: new_id("rem"))
    incident_id: str
    hypothesis_id: str
    type: RemediationType
    title: str
    description: str
    diff: str | None = None
    config_change: dict[str, Any] | None = None
    validation_status: str | None = None
    validation_detail: str | None = None


class IncidentFingerprint(DomainModel):
    services: list[str] = Field(default_factory=list)
    metric_patterns: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None


class IncidentMemoryRecord(DomainModel):
    id: str = Field(default_factory=lambda: new_id("mem"))
    incident_id: str
    fingerprint: IncidentFingerprint
    symptoms: list[Symptom] = Field(default_factory=list)
    evidence_summary: list[str] = Field(default_factory=list)
    root_cause: str
    experiment_summary: str
    verified_intervention: str
    remediation_summary: str
    post_fix_metrics: TelemetrySnapshot | None = None
    created_at: datetime = Field(default_factory=now)


class AgentRun(DomainModel):
    id: str = Field(default_factory=lambda: new_id("agent"))
    agent: str
    model: str
    incident_id: str
    started_at: datetime = Field(default_factory=now)
    completed_at: datetime | None = None
    latency_ms: int | None = None
    status: str
    error: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    output_validation_status: Literal["validated", "repaired", "failed"] | None = None


class TimelineEvent(DomainModel):
    id: str = Field(default_factory=lambda: new_id("evt"))
    incident_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=now)
    title: str
    description: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    state: InvestigationState | None = None


class CounterfactualResult(DomainModel):
    scenario_label: str
    actual_failed_requests: int
    counterfactual_failed_requests: int
    estimated_avoided_failures: int
    intervention_time_offset_seconds: int
    note: str

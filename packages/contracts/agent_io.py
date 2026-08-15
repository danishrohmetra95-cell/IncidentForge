"""Agent input/output contracts.

Every agent returns structured data validated against these schemas.
Pipeline: model output → JSON parse → Pydantic validation → repair/retry → domain object.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .domain import (
    Evidence,
    EvidenceType,
    ExperimentControls,
    Hypothesis,
    InterventionSpec,
    MetricDirection,
    MetricExpectation,
    Prediction,
    RemediationType,
    Severity,
    Symptom,
)


# ---------------------------------------------------------------------------
# Triage Agent
# ---------------------------------------------------------------------------

class TriageInput(BaseModel):
    incident_title: str
    incident_description: str
    service: str
    initial_telemetry: dict[str, float] = Field(default_factory=dict)
    recent_events: list[str] = Field(default_factory=list)


class TriageOutput(BaseModel):
    """The triage agent classifies the incident. It MUST NOT declare a root cause."""
    incident_type: str
    estimated_severity: Severity
    affected_services: list[str]
    symptoms: list[Symptom]
    abnormal_metrics: list[str]
    recent_relevant_events: list[str]
    summary: str


# ---------------------------------------------------------------------------
# Evidence Analyst
# ---------------------------------------------------------------------------

class EvidenceAnalysisInput(BaseModel):
    incident_id: str
    triage_summary: str
    symptoms: list[Symptom]
    scenario_data: dict = Field(default_factory=dict)
    historical_incidents: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    type: EvidenceType
    source: str
    observation: str
    strength: float = Field(ge=0.0, le=1.0)
    supports_hypotheses: list[str] = Field(default_factory=list)
    contradicts_hypotheses: list[str] = Field(default_factory=list)


class EvidenceAnalysisOutput(BaseModel):
    evidence: list[EvidenceItem]
    correlations: list[str]
    timeline_observations: list[str]
    gaps: list[str]


# ---------------------------------------------------------------------------
# Hypothesis Engine
# ---------------------------------------------------------------------------

class HypothesisGenerationInput(BaseModel):
    incident_id: str
    triage_summary: str
    symptoms: list[Symptom]
    evidence: list[Evidence]


class HypothesisCandidate(BaseModel):
    statement: str
    initial_score: float = Field(ge=0.0, le=1.0)
    supporting_evidence_indices: list[int] = Field(default_factory=list)
    contradicting_evidence_indices: list[int] = Field(default_factory=list)
    predictions: list[Prediction]
    reasoning: str


class HypothesisGenerationOutput(BaseModel):
    hypotheses: list[HypothesisCandidate]
    rationale: str


# ---------------------------------------------------------------------------
# Adversarial Critic
# ---------------------------------------------------------------------------

class CritiqueInput(BaseModel):
    incident_id: str
    leading_hypothesis: Hypothesis
    all_hypotheses: list[Hypothesis]
    evidence: list[Evidence]


class CritiqueOutput(BaseModel):
    """The critic MUST attempt to falsify, not merely summarize."""
    hypothesis_id: str
    objections: list[str]
    assumptions_identified: list[str]
    evidence_weaknesses: list[str]
    contradictions: list[str]
    alternative_explanations: list[str]
    falsification_criteria: list[str]
    recommended_experiment_description: str
    recommended_intervention_type: str


# ---------------------------------------------------------------------------
# Experiment Designer
# ---------------------------------------------------------------------------

class ExperimentDesignInput(BaseModel):
    incident_id: str
    target_hypothesis: Hypothesis
    critique: CritiqueOutput
    available_interventions: list[str]
    current_telemetry: dict[str, float] = Field(default_factory=dict)


class ExperimentDesignOutput(BaseModel):
    target_hypothesis_id: str
    intervention: InterventionSpec
    controls: ExperimentControls
    expected_conditions: list[MetricExpectation]
    observation_window_seconds: int = 10
    failure_conditions: list[str] = Field(default_factory=list)
    rationale: str


# ---------------------------------------------------------------------------
# Remediation Agent
# ---------------------------------------------------------------------------

class RemediationInput(BaseModel):
    incident_id: str
    verified_hypothesis: Hypothesis
    root_cause_evidence: list[Evidence]
    experiment_summary: str
    service: str


class RemediationOutput(BaseModel):
    type: RemediationType
    title: str
    description: str
    diff: str | None = None
    config_change: dict | None = None
    verification_steps: list[str] = Field(default_factory=list)
    expected_metric_improvements: list[str] = Field(default_factory=list)

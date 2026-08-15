from datetime import datetime
from typing import Any
from sqlalchemy import Text, Float, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from apps.api.database import Base

class IncidentModel(Base):
    __tablename__ = "incidents"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    service: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scenario_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    evidence = relationship("EvidenceModel", back_populates="incident")
    hypotheses = relationship("HypothesisModel", back_populates="incident")
    experiments = relationship("ExperimentModel", back_populates="incident")
    remediations = relationship("RemediationModel", back_populates="incident")

class EvidenceModel(Base):
    __tablename__ = "evidence"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    strength: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)
    
    incident = relationship("IncidentModel", back_populates="evidence")

class HypothesisModel(Base):
    __tablename__ = "hypotheses"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    predictions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    alternatives: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    
    incident = relationship("IncidentModel", back_populates="hypotheses")
    experiments = relationship("ExperimentModel", back_populates="hypothesis")

class CritiqueModel(Base):
    __tablename__ = "critiques"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.id"), index=True, nullable=False)
    objections: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    assumptions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    evidence_weaknesses: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    contradictions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    alternatives: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    falsification_criteria: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    recommended_experiment: Mapped[str] = mapped_column(Text, nullable=False)

    hypothesis = relationship("HypothesisModel")

class ExperimentModel(Base):
    __tablename__ = "experiments"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True, nullable=False)
    target_hypothesis: Mapped[str] = mapped_column(ForeignKey("hypotheses.id"), nullable=False)
    intervention: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    controls: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    baseline: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    expected_conditions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    observation_window: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    
    incident = relationship("IncidentModel", back_populates="experiments")
    hypothesis = relationship("HypothesisModel", back_populates="experiments")
    observations = relationship("ExperimentObservationModel", back_populates="experiment")

class ExperimentObservationModel(Base):
    __tablename__ = "experiment_observations"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    baseline: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    post_intervention: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    duration: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_snapshots: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    
    experiment = relationship("ExperimentModel", back_populates="observations")

class RemediationModel(Base):
    __tablename__ = "remediations"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True, nullable=False)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.id"), nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    diff: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_change: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    incident = relationship("IncidentModel", back_populates="remediations")
    hypothesis = relationship("HypothesisModel")

class IncidentMemoryModel(Base):
    __tablename__ = "incident_memories"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True, nullable=False)
    fingerprint: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    symptoms: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    evidence_summary: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    experiment_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_intervention: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_fix_metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    embedding = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class AgentRunModel(Base):
    __tablename__ = "agent_runs"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    agent: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_validation_status: Mapped[str | None] = mapped_column(Text, nullable=True)

class TimelineEventModel(Base):
    __tablename__ = "timeline_events"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)

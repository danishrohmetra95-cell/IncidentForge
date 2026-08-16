import logging
from typing import Any, Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from packages.contracts.domain import (
    Incident, Evidence, Hypothesis, Critique, Experiment, Observation, VerificationResult,
    Remediation, TimelineEvent, IncidentMemoryRecord, AgentRun, InvestigationState,
    Severity, EvidenceType, HypothesisStatus, MetricDirection, Prediction,
    InterventionSpec, ExperimentControls, MetricExpectation, TelemetrySnapshot,
    ConditionResult, VerificationOutcome, RemediationType, IncidentFingerprint,
    LiveApplicationObservation
)
from packages.orchestration.orchestrator import InvestigationContext
from apps.api.database import async_sessionmaker_factory
from apps.api.persistence.models import (
    IncidentModel, EvidenceModel, HypothesisModel, ExperimentModel,
    ExperimentObservationModel, RemediationModel, TimelineEventModel,
    IncidentMemoryModel, AgentRunModel, CritiqueModel
)

logger = logging.getLogger(__name__)

class IncidentRepository:
    def __init__(self, memory_store: Any | None = None):
        self._db_available = True
        
        # In-memory fallbacks
        self._incidents: dict[str, Incident] = {}
        self._contexts: dict[str, InvestigationContext] = {}
        self._evidence: dict[str, list[Evidence]] = {}
        self._hypotheses: dict[str, list[Hypothesis]] = {}
        self._critiques: dict[str, list[Critique]] = {}
        self._experiments: dict[str, list[Experiment]] = {}
        self._observations: dict[str, list[Observation]] = {}
        self._verifications: dict[str, list[VerificationResult]] = {}
        self._remediations: dict[str, Remediation] = {}
        self._timelines: dict[str, list[TimelineEvent]] = {}
        self._memories: dict[str, IncidentMemoryRecord] = {}
        self._agent_runs: dict[str, list[AgentRun]] = {}
        self._live_observations: dict[str, LiveApplicationObservation] = {}
        # One memory implementation owns similarity policy.  A repository may
        # receive the application singleton; standalone repositories retain an
        # isolated in-memory store for tests and offline use.
        if memory_store is None:
            from packages.memory.store import IncidentMemoryStore
            memory_store = IncidentMemoryStore()
        self._memory_store = memory_store

    async def _check_db(self):
        if not self._db_available:
            return False
        try:
            async with async_sessionmaker_factory() as session:
                await session.execute(select(1))
            return True
        except Exception:
            self._db_available = False
            return False

    async def health_status(self) -> dict[str, bool]:
        """Report the persistence mode actually available to this process."""
        database_available = await self._check_db()
        return {
            "database_available": database_available,
            "in_memory_fallback": not database_available,
        }

    async def save_incident(self, incident: Incident) -> None:
        if not await self._check_db():
            self._incidents[incident.id] = incident
            return
            
        try:
            async with async_sessionmaker_factory() as session:
                stmt = select(IncidentModel).where(IncidentModel.id == incident.id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if not model:
                    model = IncidentModel(id=incident.id)
                    session.add(model)
                model.title = incident.title
                model.description = incident.description
                model.severity = incident.severity.value
                model.service = incident.service
                model.status = incident.status.value
                model.created_at = incident.created_at
                model.resolved_at = incident.resolved_at
                model.scenario_id = incident.scenario_id
                await session.commit()
                self._incidents[incident.id] = incident
        except SQLAlchemyError as e:
            logger.warning(f"Failed to save incident to DB: {e}")
            self._db_available = False
            self._incidents[incident.id] = incident

    async def get_incident(self, incident_id: str) -> Incident | None:
        if not await self._check_db():
            return self._incidents.get(incident_id)
            
        try:
            async with async_sessionmaker_factory() as session:
                stmt = select(IncidentModel).where(IncidentModel.id == incident_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()
                if not model:
                    return None
                
                incident = Incident(
                    id=model.id,
                    title=model.title,
                    description=model.description,
                    severity=Severity(model.severity),
                    service=model.service,
                    status=InvestigationState(model.status),
                    created_at=model.created_at,
                    resolved_at=model.resolved_at,
                    scenario_id=model.scenario_id
                )
                self._incidents[incident.id] = incident
                return incident
        except SQLAlchemyError as e:
            logger.warning(f"Failed to get incident from DB: {e}")
            self._db_available = False
            return self._incidents.get(incident_id)

    async def list_incidents(self) -> list[Incident]:
        if not await self._check_db():
            return list(self._incidents.values())
            
        try:
            async with async_sessionmaker_factory() as session:
                stmt = select(IncidentModel)
                result = await session.execute(stmt)
                models = result.scalars().all()
                incidents = []
                for model in models:
                    incident = Incident(
                        id=model.id,
                        title=model.title,
                        description=model.description,
                        severity=Severity(model.severity),
                        service=model.service,
                        status=InvestigationState(model.status),
                        created_at=model.created_at,
                        resolved_at=model.resolved_at,
                        scenario_id=model.scenario_id
                    )
                    self._incidents[incident.id] = incident
                    incidents.append(incident)
                return incidents
        except SQLAlchemyError as e:
            logger.warning(f"Failed to list incidents from DB: {e}")
            self._db_available = False
            return list(self._incidents.values())

    async def save_context(self, ctx: InvestigationContext) -> None:
        self._contexts[ctx.incident.id] = ctx
        await self.save_incident(ctx.incident)
        
        self._evidence[ctx.incident.id] = ctx.evidence
        self._hypotheses[ctx.incident.id] = ctx.hypotheses
        self._critiques[ctx.incident.id] = ctx.critiques
        self._experiments[ctx.incident.id] = ctx.experiments
        self._observations[ctx.incident.id] = ctx.observations
        self._verifications[ctx.incident.id] = ctx.verifications
        if ctx.remediation:
            self._remediations[ctx.incident.id] = ctx.remediation
        self._timelines[ctx.incident.id] = ctx.timeline
        self._agent_runs[ctx.incident.id] = ctx.agent_runs

        if not await self._check_db():
            return

        try:
            async with async_sessionmaker_factory() as session:
                for ev in ctx.evidence:
                    stmt = select(EvidenceModel).where(EvidenceModel.id == ev.id)
                    model = (await session.execute(stmt)).scalar_one_or_none()
                    if not model:
                        model = EvidenceModel(id=ev.id, incident_id=ctx.incident.id)
                        session.add(model)
                    model.type = ev.type.value
                    model.source = ev.source
                    model.observation = ev.observation
                    model.timestamp = ev.timestamp
                    model.strength = str(ev.strength)
                    model.metadata_ = ev.metadata
                
                for hyp in ctx.hypotheses:
                    stmt = select(HypothesisModel).where(HypothesisModel.id == hyp.id)
                    model = (await session.execute(stmt)).scalar_one_or_none()
                    if not model:
                        model = HypothesisModel(id=hyp.id, incident_id=ctx.incident.id)
                        session.add(model)
                    model.statement = hyp.statement
                    model.status = hyp.status.value
                    model.score = hyp.score
                    model.predictions = [p.model_dump() for p in hyp.predictions]
                    model.alternatives = hyp.alternatives

                for critique in ctx.critiques:
                    stmt = select(CritiqueModel).where(CritiqueModel.id == critique.id)
                    model = (await session.execute(stmt)).scalar_one_or_none()
                    if not model:
                        model = CritiqueModel(id=critique.id, hypothesis_id=critique.hypothesis_id)
                        session.add(model)
                    model.objections = critique.objections
                    model.assumptions = critique.assumptions
                    model.evidence_weaknesses = critique.evidence_weaknesses
                    model.contradictions = critique.contradictions
                    model.alternatives = critique.alternatives
                    model.falsification_criteria = critique.falsification_criteria
                    model.recommended_experiment = critique.recommended_experiment
                
                for exp in ctx.experiments:
                    stmt = select(ExperimentModel).where(ExperimentModel.id == exp.id)
                    model = (await session.execute(stmt)).scalar_one_or_none()
                    if not model:
                        model = ExperimentModel(id=exp.id, incident_id=ctx.incident.id, target_hypothesis=exp.target_hypothesis)
                        session.add(model)
                    model.intervention = exp.intervention.model_dump()
                    model.controls = exp.controls.model_dump()
                    model.baseline = exp.baseline
                    model.expected_conditions = [c.model_dump() for c in exp.expected_conditions]
                    model.observation_window = str(exp.observation_window_seconds)
                    model.status = exp.status

                for obs in ctx.observations:
                    stmt = select(ExperimentObservationModel).where(ExperimentObservationModel.id == obs.id)
                    model = (await session.execute(stmt)).scalar_one_or_none()
                    if not model:
                        model = ExperimentObservationModel(id=obs.id, experiment_id=obs.experiment_id)
                        session.add(model)
                    model.baseline = obs.baseline.model_dump()
                    model.post_intervention = obs.post_intervention.model_dump()
                    model.duration = str(obs.duration_seconds)
                    model.raw_snapshots = [s.model_dump() for s in obs.raw_snapshots]
                
                if ctx.remediation:
                    rem = ctx.remediation
                    stmt = select(RemediationModel).where(RemediationModel.id == rem.id)
                    model = (await session.execute(stmt)).scalar_one_or_none()
                    if not model:
                        model = RemediationModel(id=rem.id, incident_id=ctx.incident.id, hypothesis_id=rem.hypothesis_id)
                        session.add(model)
                    model.type = rem.type.value
                    model.title = rem.title
                    model.description = rem.description
                    model.diff = rem.diff
                    model.config_change = rem.config_change
                    model.validation_status = rem.validation_status
                    model.validation_detail = rem.validation_detail

                for evt in ctx.timeline:
                    stmt = select(TimelineEventModel).where(TimelineEventModel.id == evt.id)
                    model = (await session.execute(stmt)).scalar_one_or_none()
                    if not model:
                        model = TimelineEventModel(id=evt.id, incident_id=ctx.incident.id)
                        session.add(model)
                    model.event_type = evt.event_type
                    model.timestamp = evt.timestamp
                    model.title = evt.title
                    model.description = evt.description
                    model.data = evt.data
                    model.state = evt.state.value if evt.state else None

                for run in ctx.agent_runs:
                    stmt = select(AgentRunModel).where(AgentRunModel.id == run.id)
                    model = (await session.execute(stmt)).scalar_one_or_none()
                    if not model:
                        model = AgentRunModel(id=run.id, incident_id=ctx.incident.id)
                        session.add(model)
                    model.agent = run.agent
                    model.model = run.model
                    model.started_at = run.started_at
                    model.completed_at = run.completed_at
                    model.latency_ms = run.latency_ms
                    model.status = run.status
                    model.error = run.error
                    model.input_tokens = run.input_tokens
                    model.output_tokens = run.output_tokens
                    model.output_validation_status = run.output_validation_status

                await session.commit()
                
        except SQLAlchemyError as e:
            logger.warning(f"Failed to save context to DB: {e}")
            self._db_available = False

    async def get_evidence(self, incident_id: str) -> list[Evidence]:
        return self._evidence.get(incident_id, [])

    async def get_hypotheses(self, incident_id: str) -> list[Hypothesis]:
        return self._hypotheses.get(incident_id, [])

    async def get_critiques(self, incident_id: str) -> list[Critique]:
        return self._critiques.get(incident_id, [])

    async def get_experiments(self, incident_id: str) -> list[Experiment]:
        return self._experiments.get(incident_id, [])

    async def get_observations(self, experiment_id: str) -> list[Observation]:
        return self._observations.get(experiment_id, [])

    async def get_verifications(self, experiment_id: str) -> list[VerificationResult]:
        return self._verifications.get(experiment_id, [])

    async def get_remediation(self, incident_id: str) -> Remediation | None:
        return self._remediations.get(incident_id)

    async def get_timeline(self, incident_id: str) -> list[TimelineEvent]:
        return self._timelines.get(incident_id, [])

    async def save_memory(self, record: IncidentMemoryRecord) -> None:
        self._memories[record.incident_id] = record
        await self._memory_store.store(record)
        if not await self._check_db():
            return
            
        try:
            async with async_sessionmaker_factory() as session:
                stmt = select(IncidentMemoryModel).where(IncidentMemoryModel.id == record.id)
                model = (await session.execute(stmt)).scalar_one_or_none()
                if not model:
                    model = IncidentMemoryModel(id=record.id, incident_id=record.incident_id)
                    session.add(model)
                model.fingerprint = record.fingerprint.model_dump() if record.fingerprint else None
                model.symptoms = [s.model_dump() for s in record.symptoms] if record.symptoms else []
                model.evidence_summary = record.evidence_summary
                model.root_cause = record.root_cause
                model.experiment_summary = record.experiment_summary
                model.verified_intervention = record.verified_intervention
                model.remediation_summary = record.remediation_summary
                model.post_fix_metrics = record.post_fix_metrics.model_dump() if record.post_fix_metrics else None
                model.embedding = record.fingerprint.embedding if record.fingerprint and record.fingerprint.embedding else None
                model.created_at = record.created_at
                await session.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Failed to save memory to DB: {e}")
            self._db_available = False

    async def get_memory(self, incident_id: str) -> IncidentMemoryRecord | None:
        return await self._memory_store.get_by_incident(incident_id)

    async def find_similar_memories(self, fingerprint: Any, limit: int) -> list[IncidentMemoryRecord]:
        return await self._memory_store.find_similar(fingerprint, limit=limit)

    async def save_agent_run(self, run: AgentRun) -> None:
        if run.incident_id not in self._agent_runs:
            self._agent_runs[run.incident_id] = []
        self._agent_runs[run.incident_id].append(run)
        
        if not await self._check_db():
            return
            
        try:
            async with async_sessionmaker_factory() as session:
                stmt = select(AgentRunModel).where(AgentRunModel.id == run.id)
                model = (await session.execute(stmt)).scalar_one_or_none()
                if not model:
                    model = AgentRunModel(id=run.id, incident_id=run.incident_id)
                    session.add(model)
                model.agent = run.agent
                model.model = run.model
                model.started_at = run.started_at
                model.completed_at = run.completed_at
                model.latency_ms = run.latency_ms
                model.status = run.status
                model.error = run.error
                model.input_tokens = run.input_tokens
                model.output_tokens = run.output_tokens
                model.output_validation_status = run.output_validation_status
                await session.commit()
        except SQLAlchemyError as e:
            logger.warning(f"Failed to save agent run to DB: {e}")
            self._db_available = False

    async def save_live_observation(self, observation: LiveApplicationObservation) -> None:
        self._live_observations[observation.id] = observation

    async def get_live_observation(self, observation_id: str) -> LiveApplicationObservation | None:
        return self._live_observations.get(observation_id)


_repository_instance = None

def get_repository() -> IncidentRepository:
    global _repository_instance
    if _repository_instance is None:
        from apps.api.services import get_memory_store
        _repository_instance = IncidentRepository(memory_store=get_memory_store())
    return _repository_instance

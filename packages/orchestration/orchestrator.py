"""Investigation orchestrator.

The central coordination loop that drives an incident investigation
through the complete lifecycle. Agents are invoked at each phase;
deterministic software controls state transitions, simulation,
verification, and confidence scoring.

LLMs propose. Deterministic software verifies.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Coroutine

from packages.contracts.domain import (
    AgentRun,
    Critique,
    Evidence,
    Experiment,
    Hypothesis,
    HypothesisStatus,
    Incident,
    IncidentMemoryRecord,
    InvestigationState,
    MetricExpectation,
    Observation,
    Remediation,
    RemediationType,
    TelemetrySnapshot,
    TimelineEvent,
    VerificationOutcome,
    VerificationResult,
    now,
    new_id,
)
from packages.contracts.events import (
    InvestigationEvent,
    incident_created,
    triage_started,
    triage_completed,
    evidence_found,
    hypothesis_created,
    hypothesis_updated,
    critic_started,
    critic_completed,
    experiment_proposed,
    experiment_validated,
    experiment_started,
    experiment_completed,
    belief_updated,
    remediation_generated,
    remediation_validated,
    incident_resolved,
    investigation_failed,
)
from packages.contracts.agent_io import (
    TriageInput,
    TriageOutput,
    EvidenceAnalysisInput,
    EvidenceAnalysisOutput,
    HypothesisGenerationInput,
    HypothesisGenerationOutput,
    CritiqueInput,
    CritiqueOutput,
    ExperimentDesignInput,
    ExperimentDesignOutput,
    RemediationInput,
    RemediationOutput,
)
from packages.orchestration.state_machine import InvestigationStateMachine

logger = logging.getLogger("incidentforge.orchestrator")

# Maximum retry cycles when hypothesis is rejected or inconclusive
MAX_HYPOTHESIS_CYCLES = 3
# Maximum experiment attempts per hypothesis (safety rejections + inconclusive)
MAX_EXPERIMENT_ATTEMPTS = 3
# Maximum remediation validation retries
MAX_REMEDIATION_RETRIES = 2


class InvestigationContext:
    """Mutable context accumulating artifacts during an investigation."""

    def __init__(self, incident: Incident):
        self.incident = incident
        self.state_machine = InvestigationStateMachine()
        self.triage: TriageOutput | None = None
        self.evidence: list[Evidence] = []
        self.hypotheses: list[Hypothesis] = []
        self.critiques: list[Critique] = []
        self.experiments: list[Experiment] = []
        self.observations: list[Observation] = []
        self.verifications: list[VerificationResult] = []
        self.remediation: Remediation | None = None
        self.timeline: list[TimelineEvent] = []
        self.agent_runs: list[AgentRun] = []
        self.hypothesis_cycles = 0


# Type for event listener callbacks
EventListener = Callable[[InvestigationEvent], Coroutine[Any, Any, None]]


class InvestigationOrchestrator:
    """Drives the complete investigation lifecycle.

    This is the coordination layer — it invokes agents, feeds their outputs
    to deterministic engines, and controls state transitions. The orchestrator
    does NOT perform reasoning; it delegates to agents (AI) and engines
    (deterministic software).
    """

    def __init__(
        self,
        # Agents
        triage_agent: Any,
        evidence_analyst: Any,
        hypothesis_engine: Any,
        adversarial_critic: Any,
        experiment_designer: Any,
        remediation_agent: Any,
        # Deterministic engines
        experiment_engine: Any,
        verification_engine: Any,
        belief_engine: Any,
        safety_validator: Any,
        # Digital Twin
        twin_factory: Any,      # callable returning configured DigitalTwin
        # Memory
        memory_store: Any | None = None,
        fingerprinter: Any | None = None,
        # Event system
        event_listeners: list[EventListener] | None = None,
        # Fallback agents
        fallback_agents: Any | None = None,
    ):
        self._triage = triage_agent
        self._evidence = evidence_analyst
        self._hypothesis = hypothesis_engine
        self._critic = adversarial_critic
        self._experiment_designer = experiment_designer
        self._remediation = remediation_agent
        self._experiment_engine = experiment_engine
        self._verification = verification_engine
        self._belief = belief_engine
        self._safety = safety_validator
        self._twin_factory = twin_factory
        self._memory = memory_store
        self._fingerprinter = fingerprinter
        self._listeners: list[EventListener] = event_listeners or []
        self._fallback_agents = fallback_agents

    def add_listener(self, listener: EventListener) -> None:
        self._listeners.append(listener)

    async def _emit(self, event: InvestigationEvent) -> None:
        for listener in self._listeners:
            try:
                await listener(event)
            except Exception:
                logger.warning("Event listener error", exc_info=True)

    def _timeline(self, ctx: InvestigationContext, event_type: str,
                  title: str, description: str = "", **data: Any) -> None:
        entry = TimelineEvent(
            incident_id=ctx.incident.id,
            event_type=event_type,
            title=title,
            description=description,
            data=data,
            state=ctx.state_machine.state,
        )
        ctx.timeline.append(entry)

    async def _run_agent(self, ctx: InvestigationContext, agent_name: str,
                         model_name: str, coro: Any, fallback_func: Any = None) -> Any:
        """Execute an agent call and record telemetry."""
        run = AgentRun(
            agent=agent_name,
            model=model_name,
            incident_id=ctx.incident.id,
            status="running",
        )
        start = time.monotonic()
        from packages.llm.structured import output_validation_status
        output_validation_status.set("validated")
        try:
            result = await coro
            elapsed_ms = int((time.monotonic() - start) * 1000)
            run.completed_at = now()
            run.latency_ms = elapsed_ms
            run.status = "completed"
            # Live gateway parsing distinguishes clean schema validation from
            # a repaired response. Deterministic agents produce typed
            # contracts directly and therefore validate cleanly.
            run.output_validation_status = output_validation_status.get()
            ctx.agent_runs.append(run)
            return result
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            run.completed_at = now()
            run.latency_ms = elapsed_ms
            
            if fallback_func is not None:
                logger.warning("Live reasoning failed (%s), falling back to deterministic mode for %s", exc, agent_name)
                # Retry with fallback
                run.status = "fallback"
                ctx.agent_runs.append(run)
                return await fallback_func()
                
            run.status = "failed"
            run.error = str(exc)
            run.output_validation_status = "failed"
            ctx.agent_runs.append(run)
            raise

    async def run(self, incident: Incident, scenario_data: dict | None = None, initial_context: InvestigationContext | None = None) -> InvestigationContext:
        """Execute the complete investigation lifecycle."""
        ctx = initial_context or InvestigationContext(incident)
        scenario = scenario_data or {}

        try:
            await self._emit(incident_created(incident.id, title=incident.title))
            self._timeline(ctx, "incident.created", "Incident created",
                           incident.title)

            # ── INGEST ──────────────────────────────────────────────
            ctx.state_machine.transition(InvestigationState.INGESTING)
            ctx.incident.status = InvestigationState.INGESTING
            self._timeline(ctx, "phase.started", "Ingesting incident data")

            # ── TRIAGE ──────────────────────────────────────────────
            ctx.state_machine.transition(InvestigationState.TRIAGING)
            ctx.incident.status = InvestigationState.TRIAGING
            await self._emit(triage_started(incident.id))

            triage_input = TriageInput(
                incident_title=incident.title,
                incident_description=incident.description,
                service=incident.service,
                initial_telemetry=scenario.get("initial_telemetry", {}),
                recent_events=scenario.get("recent_events", []),
            )
            ctx.triage = await self._run_agent(
                ctx, "triage", "fast_reasoning",
                self._triage.analyze(triage_input),
                fallback_func=lambda: self._fallback_agents.analyze(triage_input) if self._fallback_agents else None
            )
            ctx.incident.symptoms = ctx.triage.symptoms
            if ctx.triage.estimated_severity:
                ctx.incident.severity = ctx.triage.estimated_severity

            await self._emit(triage_completed(
                incident.id, summary=ctx.triage.summary
            ))
            self._timeline(ctx, "triage.completed", "Triage complete",
                           ctx.triage.summary)

            # ── EVIDENCE COLLECTION ─────────────────────────────────
            ctx.state_machine.transition(InvestigationState.EVIDENCE_COLLECTION)
            ctx.incident.status = InvestigationState.EVIDENCE_COLLECTION

            # Fetch similar historical incidents for context
            historical = []
            if self._memory and self._fingerprinter:
                fp = self._fingerprinter.fingerprint(
                    ctx.incident, ctx.triage.symptoms, []
                )
                similar = await self._memory.find_similar(fp, limit=3)
                historical = [
                    f"INC-{s.incident_id[:8]}: {s.root_cause}" for s in similar
                ]

            evidence_input = EvidenceAnalysisInput(
                incident_id=incident.id,
                triage_summary=ctx.triage.summary,
                symptoms=ctx.triage.symptoms,
                scenario_data=scenario,
                historical_incidents=historical,
            )
            evidence_output = await self._run_agent(
                ctx, "evidence_analyst", "fast_reasoning",
                self._evidence.analyze(evidence_input),
                fallback_func=lambda: self._fallback_agents.analyze_evidence(evidence_input) if self._fallback_agents else None
            )

            for item in evidence_output.evidence:
                ev = Evidence(
                    incident_id=incident.id,
                    type=item.type,
                    source=item.source,
                    observation=item.observation,
                    strength=item.strength,
                )
                ctx.evidence.append(ev)
                await self._emit(evidence_found(
                    incident.id, ev.id, ev.observation[:100]
                ))

            self._timeline(ctx, "evidence.collected",
                           f"Collected {len(ctx.evidence)} evidence items")

            # ── HYPOTHESIS-EXPERIMENT CYCLE ─────────────────────────
            # Outer loop: hypothesis generation / re-generation on REJECTED
            # Inner loop: experiment design / execution on INCONCLUSIVE or safety rejection
            verified = await self._hypothesis_experiment_cycle(ctx, incident, scenario)

            if not verified:
                return ctx

            # ── REMEDIATION ─────────────────────────────────────────
            verified_hyp = next(
                (h for h in ctx.hypotheses if h.status == HypothesisStatus.VERIFIED),
                None,
            )
            if not verified_hyp:
                await self._fail(ctx, "No verified hypothesis found")
                return ctx

            await self._remediation_phase(ctx, incident, scenario, verified_hyp)

        except Exception as exc:
            logger.error("Investigation failed: %s", exc, exc_info=True)
            await self._fail(ctx, f"Unexpected error: {exc}")

        return ctx

    async def _hypothesis_experiment_cycle(
        self, ctx: InvestigationContext, incident: Incident, scenario: dict,
    ) -> bool:
        """Run the nested hypothesis → critique → experiment cycle.

        Returns True if a hypothesis was verified, False otherwise.
        """
        while ctx.hypothesis_cycles < MAX_HYPOTHESIS_CYCLES:
            ctx.hypothesis_cycles += 1

            # ── HYPOTHESIS GENERATION ───────────────────────────
            ctx.state_machine.transition(InvestigationState.HYPOTHESIS_GENERATION)
            ctx.incident.status = InvestigationState.HYPOTHESIS_GENERATION

            hyp_input = HypothesisGenerationInput(
                incident_id=incident.id,
                triage_summary=ctx.triage.summary,
                symptoms=ctx.triage.symptoms,
                evidence=ctx.evidence,
            )
            hyp_output = await self._run_agent(
                ctx, "hypothesis_engine", "deep_reasoning",
                self._hypothesis.generate(hyp_input),
                fallback_func=lambda: self._fallback_agents.generate_hypotheses(hyp_input) if self._fallback_agents else None
            )

            ctx.hypotheses = []
            for candidate in hyp_output.hypotheses:
                h = Hypothesis(
                    incident_id=incident.id,
                    statement=candidate.statement,
                    score=candidate.initial_score,
                    predictions=candidate.predictions,
                )
                # Link evidence
                for idx in candidate.supporting_evidence_indices:
                    if idx < len(ctx.evidence):
                        h.supporting_evidence.append(ctx.evidence[idx].id)
                for idx in candidate.contradicting_evidence_indices:
                    if idx < len(ctx.evidence):
                        h.contradicting_evidence.append(ctx.evidence[idx].id)

                ctx.hypotheses.append(h)
                await self._emit(hypothesis_created(
                    incident.id, h.id, h.statement, h.score
                ))

            self._timeline(ctx, "hypotheses.generated",
                           f"Generated {len(ctx.hypotheses)} hypotheses")

            if not ctx.hypotheses:
                if incident.reasoning_mode == "live_model":
                    self._timeline(ctx, "hypotheses.none", "No causal hypothesis could be established from external telemetry.")
                    # Leave status as HYPOTHESIS_GENERATION or transition to something else, but don't FAIL
                    ctx.state_machine.transition(InvestigationState.RESOLVED)
                    ctx.incident.status = InvestigationState.RESOLVED
                    return False
                await self._fail(ctx, "No hypotheses generated")
                return False

            # ── ADVERSARIAL CRITIQUE ────────────────────────────
            ctx.state_machine.transition(InvestigationState.HYPOTHESIS_CRITIQUE)
            ctx.incident.status = InvestigationState.HYPOTHESIS_CRITIQUE
            await self._emit(critic_started(incident.id))

            leading = max(ctx.hypotheses, key=lambda h: h.score)
            leading.status = HypothesisStatus.TESTING

            critique_input = CritiqueInput(
                incident_id=incident.id,
                leading_hypothesis=leading,
                all_hypotheses=ctx.hypotheses,
                evidence=ctx.evidence,
            )
            critique_output = await self._run_agent(
                ctx, "adversarial_critic", "deep_reasoning",
                self._critic.critique(critique_input),
                fallback_func=lambda: self._fallback_agents.critique(critique_input) if self._fallback_agents else None
            )
            critique = Critique(
                hypothesis_id=leading.id,
                objections=critique_output.objections,
                assumptions=critique_output.assumptions_identified,
                evidence_weaknesses=critique_output.evidence_weaknesses,
                contradictions=critique_output.contradictions,
                alternatives=critique_output.alternative_explanations,
                falsification_criteria=critique_output.falsification_criteria,
                recommended_experiment=critique_output.recommended_experiment_description,
            )
            ctx.critiques.append(critique)

            await self._emit(critic_completed(
                incident.id,
                objections=critique.objections,
                alternatives=critique.alternatives,
                recommended_experiment=critique.recommended_experiment,
            ))
            self._timeline(ctx, "critic.completed",
                           "Adversarial critique complete",
                           critique.objections[0] if critique.objections else "")

            # ── INNER EXPERIMENT LOOP ───────────────────────────
            outcome = await self._experiment_loop(
                ctx, incident, scenario, leading, critique_output,
            )

            if outcome == VerificationOutcome.VERIFIED:
                return True
            elif outcome == VerificationOutcome.REJECTED:
                # Outer loop continues — re-hypothesize with updated beliefs
                # State is BELIEF_UPDATE; HYPOTHESIS_GENERATION is legal
                self._timeline(ctx, "hypothesis.rejected",
                               "Leading hypothesis rejected — re-hypothesizing")
                continue
            else:
                # Exhausted experiment attempts or no outcome
                if ctx.state_machine.state == InvestigationState.BELIEF_UPDATE:
                    # Can re-hypothesize from BELIEF_UPDATE
                    self._timeline(ctx, "experiments.exhausted",
                                   "Experiment attempts exhausted — re-hypothesizing")
                    continue
                else:
                    # Safety kept rejecting — never reached BELIEF_UPDATE
                    await self._fail(ctx, "All experiment designs rejected by safety validator")
                    return False

        # Exhausted hypothesis cycles
        await self._fail(ctx, "No verified root cause after maximum investigation cycles")
        return False

    async def _experiment_loop(
        self,
        ctx: InvestigationContext,
        incident: Incident,
        scenario: dict,
        leading: Hypothesis,
        critique_output: CritiqueOutput,
    ) -> VerificationOutcome | None:
        """Inner experiment design → execute → verify loop.

        Returns the final VerificationOutcome, or None if all attempts exhausted.
        Legal state transitions:
          HYPOTHESIS_CRITIQUE → EXPERIMENT_DESIGN → EXPERIMENT_VALIDATION
            → EXPERIMENT_EXECUTION → OBSERVATION → BELIEF_UPDATE
          BELIEF_UPDATE → EXPERIMENT_DESIGN (on INCONCLUSIVE)
          EXPERIMENT_VALIDATION → EXPERIMENT_DESIGN (on safety rejection)
        """
        experiment_attempts = 0
        last_outcome: VerificationOutcome | None = None

        while experiment_attempts < MAX_EXPERIMENT_ATTEMPTS:
            experiment_attempts += 1

            # ── EXPERIMENT DESIGN ───────────────────────────────
            ctx.state_machine.transition(InvestigationState.EXPERIMENT_DESIGN)
            ctx.incident.status = InvestigationState.EXPERIMENT_DESIGN

            available = self._experiment_engine.available_interventions()

            design_input = ExperimentDesignInput(
                incident_id=incident.id,
                target_hypothesis=leading,
                critique=critique_output,
                available_interventions=available,
                current_telemetry=scenario.get("initial_telemetry", {}),
            )
            design_output = await self._run_agent(
                ctx, "experiment_designer", "deep_reasoning",
                self._experiment_designer.design(design_input),
                fallback_func=lambda: self._fallback_agents.design(design_input) if self._fallback_agents else None
            )

            experiment = Experiment(
                incident_id=incident.id,
                target_hypothesis=leading.id,
                intervention=design_output.intervention,
                controls=design_output.controls,
                expected_conditions=design_output.expected_conditions,
                observation_window_seconds=design_output.observation_window_seconds,
                failure_conditions=design_output.failure_conditions,
            )
            ctx.experiments.append(experiment)

            await self._emit(experiment_proposed(
                incident.id, experiment.id,
                experiment.intervention.type,
            ))
            self._timeline(ctx, "experiment.designed",
                           f"Experiment: {experiment.intervention.type}",
                           design_output.rationale)

            # ── EXPERIMENT VALIDATION ───────────────────────────
            ctx.state_machine.transition(InvestigationState.EXPERIMENT_VALIDATION)
            ctx.incident.status = InvestigationState.EXPERIMENT_VALIDATION

            approved, reasons = self._safety.validate(experiment)
            experiment.status = "validated" if approved else "rejected"

            await self._emit(experiment_validated(
                incident.id, experiment.id, approved,
                "; ".join(reasons) if reasons else "",
            ))

            if not approved:
                self._timeline(ctx, "experiment.rejected",
                               "Experiment rejected by safety validator",
                               "; ".join(reasons))
                # EXPERIMENT_VALIDATION → EXPERIMENT_DESIGN is legal
                continue

            # ── EXPERIMENT EXECUTION ────────────────────────────
            ctx.state_machine.transition(InvestigationState.EXPERIMENT_EXECUTION)
            ctx.incident.status = InvestigationState.EXPERIMENT_EXECUTION
            await self._emit(experiment_started(incident.id, experiment.id))

            twin = self._twin_factory(scenario)
            observation, verification = self._experiment_engine.run(
                experiment, twin
            )
            experiment.status = "completed"

            ctx.observations.append(observation)
            ctx.verifications.append(verification)

            experiment.baseline = {
                "p95_latency": observation.baseline.p95_latency,
                "error_rate": observation.baseline.error_rate,
                "db_utilization": observation.baseline.db_utilization,
                "cpu": observation.baseline.cpu,
                "cache_hit_rate": observation.baseline.cache_hit_rate,
            }

            await self._emit(experiment_completed(
                incident.id, experiment.id,
                outcome=verification.outcome.value,
                baseline_p95=observation.baseline.p95_latency,
                post_p95=observation.post_intervention.p95_latency,
            ))
            self._timeline(ctx, "experiment.completed",
                           f"Result: {verification.outcome.value}",
                           verification.explanation)

            # ── OBSERVATION ─────────────────────────────────────
            ctx.state_machine.transition(InvestigationState.OBSERVATION)
            ctx.incident.status = InvestigationState.OBSERVATION
            self._timeline(ctx, "observation.recorded",
                           "Observation recorded")

            # ── BELIEF UPDATE ───────────────────────────────────
            ctx.state_machine.transition(InvestigationState.BELIEF_UPDATE)
            ctx.incident.status = InvestigationState.BELIEF_UPDATE

            # Build historical matches for belief update
            historical_matches = None
            if self._memory and self._fingerprinter:
                try:
                    fp = self._fingerprinter.fingerprint(
                        ctx.incident, ctx.incident.symptoms, ctx.evidence
                    )
                    similar = await self._memory.find_similar(fp, limit=5)
                    if similar:
                        # Map hypothesis IDs to whether any historical incident
                        # had a similar root cause statement
                        historical_matches = {}
                        for h in ctx.hypotheses:
                            statement_lower = h.statement.lower()
                            historical_matches[h.id] = any(
                                statement_lower in s.root_cause.lower()
                                or s.root_cause.lower() in statement_lower
                                for s in similar
                            )
                except Exception:
                    pass

            updated_scores = self._belief.update(
                ctx.hypotheses, ctx.verifications, ctx.evidence, ctx.experiments,
                historical_matches=historical_matches,
            )

            for h in ctx.hypotheses:
                if h.id in updated_scores:
                    h.score = updated_scores[h.id]

                    if h.id == leading.id:
                        if verification.outcome == VerificationOutcome.VERIFIED:
                            h.status = HypothesisStatus.VERIFIED
                        elif verification.outcome == VerificationOutcome.REJECTED:
                            h.status = HypothesisStatus.REJECTED
                        else:
                            h.status = HypothesisStatus.WEAKENED

                    await self._emit(hypothesis_updated(
                        incident.id, h.id, h.status.value, h.score
                    ))

            await self._emit(belief_updated(
                incident.id, updated_scores
            ))
            self._timeline(ctx, "belief.updated", "Confidence scores updated",
                           str(updated_scores))

            last_outcome = verification.outcome

            # ── DECISION POINT ──────────────────────────────────
            if verification.outcome == VerificationOutcome.VERIFIED:
                return VerificationOutcome.VERIFIED
            elif verification.outcome == VerificationOutcome.REJECTED:
                return VerificationOutcome.REJECTED
            else:
                # INCONCLUSIVE — try another experiment
                # BELIEF_UPDATE → EXPERIMENT_DESIGN is legal
                self._timeline(ctx, "experiment.inconclusive",
                               "Experiment inconclusive — designing new experiment")
                continue

        # Exhausted experiment attempts
        return last_outcome

    async def _remediation_phase(
        self,
        ctx: InvestigationContext,
        incident: Incident,
        scenario: dict,
        verified_hyp: Hypothesis,
    ) -> None:
        """Run remediation generation and validation with retry."""
        supporting_evidence = [
            e for e in ctx.evidence
            if e.id in verified_hyp.supporting_evidence
        ]
        last_experiment = ctx.experiments[-1] if ctx.experiments else None

        for attempt in range(MAX_REMEDIATION_RETRIES):
            ctx.state_machine.transition(InvestigationState.REMEDIATION)
            ctx.incident.status = InvestigationState.REMEDIATION

            remediation_input = RemediationInput(
                incident_id=incident.id,
                verified_hypothesis=verified_hyp,
                root_cause_evidence=supporting_evidence,
                experiment_summary=(
                    f"Intervention '{last_experiment.intervention.type}' "
                    f"resulted in {ctx.verifications[-1].outcome.value}"
                    if last_experiment else "No experiment data"
                ),
                service=incident.service,
            )
            remediation_output = await self._run_agent(
                ctx, "remediation", "deep_reasoning",
                self._remediation.generate(remediation_input),
                fallback_func=lambda: self._fallback_agents.generate_remediation(remediation_input) if self._fallback_agents else None
            )
            remediation = Remediation(
                incident_id=incident.id,
                hypothesis_id=verified_hyp.id,
                type=remediation_output.type,
                title=remediation_output.title,
                description=remediation_output.description,
                diff=remediation_output.diff,
                config_change=remediation_output.config_change,
            )
            ctx.remediation = remediation

            await self._emit(remediation_generated(
                incident.id, remediation.id, remediation.title
            ))
            self._timeline(ctx, "remediation.generated",
                           remediation.title, remediation.description)

            # ── REMEDIATION VALIDATION ──────────────────────────
            ctx.state_machine.transition(InvestigationState.REMEDIATION_VALIDATION)
            ctx.incident.status = InvestigationState.REMEDIATION_VALIDATION

            validation_passed = self._validate_remediation(
                ctx, scenario, remediation
            )
            remediation.validation_status = "validated" if validation_passed else "failed"

            await self._emit(remediation_validated(
                incident.id, remediation.id, validation_passed
            ))

            if validation_passed:
                remediation.validation_detail = "Post-fix metrics within healthy baseline"
                self._timeline(ctx, "remediation.validated",
                               "Remediation validated — metrics within healthy baseline")
                break
            else:
                remediation.validation_detail = "Post-fix metrics did not meet healthy baseline"
                self._timeline(ctx, "remediation.validation_failed",
                               f"Remediation validation failed (attempt {attempt + 1})")
                if attempt < MAX_REMEDIATION_RETRIES - 1:
                    # REMEDIATION_VALIDATION → REMEDIATION is legal
                    continue
                else:
                    await self._fail(ctx, "Remediation validation failed after retries")
                    return

        # ── RESOLVED ────────────────────────────────────────────
        ctx.state_machine.transition(InvestigationState.RESOLVED)
        ctx.incident.status = InvestigationState.RESOLVED
        ctx.incident.resolved_at = now()

        final_confidence = verified_hyp.score
        await self._emit(incident_resolved(
            incident.id, verified_hyp.statement, final_confidence
        ))
        self._timeline(ctx, "incident.resolved",
                       f"Resolved: {verified_hyp.statement}",
                       f"Confidence: {final_confidence:.0%}")

        # ── STORE IN MEMORY ─────────────────────────────────────
        if self._memory and self._fingerprinter:
            await self._store_memory(ctx, verified_hyp)

    def _validate_remediation(
        self,
        ctx: InvestigationContext,
        scenario: dict,
        remediation: Remediation,
    ) -> bool:
        """Apply remediation to a fresh twin, replay incident, check metrics.

        Lifecycle:
        1. Create fresh twin with fault injected
        2. Apply remediation (fix the root cause in simulation)
        3. Run simulation for the observation window
        4. Compare metrics against healthy baseline
        5. Return pass/fail
        """
        # Create twin with the original fault
        twin = self._twin_factory(scenario)

        # Replay the exact registered intervention whose prediction was
        # deterministically verified. A remediation document cannot inject
        # arbitrary simulator actions or modify host files.
        verified_experiment = next(
            (experiment for experiment in reversed(ctx.experiments)
             if experiment.target_hypothesis == remediation.hypothesis_id and experiment.status == "completed"),
            None,
        )
        if not verified_experiment:
            return False
        twin.apply_intervention(
            verified_experiment.intervention.type,
            verified_experiment.intervention.parameters,
        )

        # Run simulation with fix applied
        twin.tick(steps=20)
        post_fix = twin.observe()

        # Compare against healthy thresholds
        healthy_p95 = 120.0   # ms
        healthy_error = 0.02  # 2%
        healthy_cpu = 0.40

        checks = [
            post_fix.p95_latency < healthy_p95 * 3,   # within 3x of healthy
            post_fix.error_rate < healthy_error * 3,
            post_fix.cpu < healthy_cpu * 2,
        ]

        return all(checks)

    async def _store_memory(self, ctx: InvestigationContext, verified: Hypothesis) -> None:
        """Store resolved incident in memory for future retrieval."""
        fp = self._fingerprinter.fingerprint(
            ctx.incident, ctx.incident.symptoms, ctx.evidence
        )
        last_obs = ctx.observations[-1] if ctx.observations else None
        record = IncidentMemoryRecord(
            incident_id=ctx.incident.id,
            fingerprint=fp,
            symptoms=ctx.incident.symptoms,
            evidence_summary=[e.observation[:100] for e in ctx.evidence[:10]],
            root_cause=verified.statement,
            experiment_summary=(
                f"Ran {len(ctx.experiments)} experiments, "
                f"verified via {ctx.verifications[-1].outcome.value}"
                if ctx.verifications else "No experiments"
            ),
            verified_intervention=(
                ctx.experiments[-1].intervention.type
                if ctx.experiments else "none"
            ),
            remediation_summary=(
                ctx.remediation.title if ctx.remediation else "none"
            ),
            post_fix_metrics=(
                last_obs.post_intervention if last_obs else None
            ),
        )
        await self._memory.store(record)

    async def _fail(self, ctx: InvestigationContext, reason: str) -> None:
        if not ctx.state_machine.is_terminal:
            try:
                ctx.state_machine.transition(InvestigationState.FAILED)
            except Exception:
                pass
        ctx.incident.status = InvestigationState.FAILED
        self._timeline(ctx, "investigation.failed", "Investigation failed", reason)
        await self._emit(investigation_failed(ctx.incident.id, reason))
        logger.error("Investigation %s failed: %s", ctx.incident.id, reason)

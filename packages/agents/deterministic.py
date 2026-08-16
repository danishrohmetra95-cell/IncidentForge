"""Deterministic scenario reasoning adapter used only for local demo mode.

It derives structured investigation proposals from the public scenario
telemetry and incident timeline. It never reads a scenario's expected answer,
never verifies a root cause, and never executes an intervention. Those jobs
remain with the experiment, verification, and orchestration layers.
"""

from __future__ import annotations

from packages.contracts.agent_io import (
    CritiqueInput,
    CritiqueOutput,
    EvidenceAnalysisInput,
    EvidenceAnalysisOutput,
    EvidenceItem,
    ExperimentDesignInput,
    ExperimentDesignOutput,
    HypothesisCandidate,
    HypothesisGenerationInput,
    HypothesisGenerationOutput,
    RemediationInput,
    RemediationOutput,
    TriageInput,
    TriageOutput,
)
from packages.contracts.domain import (
    EvidenceType,
    ExperimentControls,
    InterventionSpec,
    MetricDirection,
    MetricExpectation,
    Prediction,
    RemediationType,
    Severity,
    Symptom,
)


class DeterministicScenarioAgents:
    """Structured local proposals for reproducible demonstrations.

    This adapter is selected only when no Featherless key is configured and
    DEMO_MODE is enabled. Production/live-model requests fail explicitly
    instead of silently using it.
    """

    async def analyze(self, input_data: TriageInput | EvidenceAnalysisInput) -> TriageOutput | EvidenceAnalysisOutput:
        if isinstance(input_data, EvidenceAnalysisInput):
            return await self.analyze_evidence(input_data)
        return await self.triage(input_data)

    async def triage(self, input_data: TriageInput) -> TriageOutput:
        metrics = input_data.initial_telemetry
        symptoms: list[Symptom] = []
        definitions = (
            ("Elevated tail latency", "p95_latency", MetricDirection.INCREASE, 250),
            ("Elevated error rate", "error_rate", MetricDirection.INCREASE, 0.02),
            ("Database pressure", "db_utilization", MetricDirection.INCREASE, 0.75),
            ("Reduced cache effectiveness", "cache_hit_rate", MetricDirection.DECREASE, 0.85),
            ("Elevated CPU", "cpu", MetricDirection.INCREASE, 0.65),
        )
        for name, metric, direction, limit in definitions:
            value = metrics.get(metric)
            abnormal = value is not None and (
                value > limit if direction == MetricDirection.INCREASE else value < limit
            )
            if abnormal:
                symptoms.append(Symptom(
                    name=name,
                    metric=metric,
                    direction=direction,
                    observed_value=float(value),
                ))

        severity = Severity.SEV_1 if metrics.get("error_rate", 0) >= 0.15 else Severity.SEV_2
        return TriageOutput(
            incident_type="checkout_service_degradation",
            estimated_severity=severity,
            affected_services=[input_data.service],
            symptoms=symptoms,
            abnormal_metrics=[symptom.metric for symptom in symptoms],
            recent_relevant_events=input_data.recent_events,
            summary=(
                "Observed user-facing degradation with correlated database, cache, "
                "and compute signals. Triage identifies symptoms only; causal "
                "explanations require competing hypotheses and experiments."
            ),
        )

    async def analyze_evidence(self, input_data: EvidenceAnalysisInput) -> EvidenceAnalysisOutput:
        telemetry = input_data.scenario_data.get("initial_telemetry", {})
        recent_events = input_data.scenario_data.get("recent_events", [])
        evidence: list[EvidenceItem] = []

        metric_names = {
            "p95_latency": "P95 latency",
            "error_rate": "Error rate",
            "db_utilization": "Database utilization",
            "cpu": "CPU utilization",
            "cache_hit_rate": "Cache hit rate",
        }
        for metric, label in metric_names.items():
            if metric in telemetry:
                evidence.append(EvidenceItem(
                    type=EvidenceType.METRIC,
                    source="digital-twin initial telemetry",
                    observation=f"{label} measured at {telemetry[metric]}.",
                    strength=0.8,
                ))

        for event in recent_events:
            event_type = EvidenceType.DEPLOYMENT if "deployment" in event.lower() else EvidenceType.LOG
            evidence.append(EvidenceItem(
                type=event_type,
                source="incident event timeline",
                observation=event,
                strength=0.6,
            ))

        return EvidenceAnalysisOutput(
            evidence=evidence,
            correlations=[
                "Latency, error rate, and database utilization rise together.",
                "Reduced cache effectiveness can increase database demand, but does not by itself prove causality.",
            ],
            timeline_observations=recent_events,
            gaps=["No direct pool lifecycle trace is available before experimentation."],
        )

    async def generate(self, input_data: HypothesisGenerationInput | RemediationInput) -> HypothesisGenerationOutput | RemediationOutput:
        if isinstance(input_data, RemediationInput):
            return await self.generate_remediation(input_data)
        return await self.generate_hypotheses(input_data)

    async def generate_hypotheses(self, input_data: HypothesisGenerationInput) -> HypothesisGenerationOutput:
        print("EVIDENCE SOURCES:", [e.source for e in input_data.evidence])
        
        text = " ".join(e.observation.lower() for e in input_data.evidence)
        is_amazon_demo = "amazon.in" in text

        is_live = any("ApplicationConnector" in e.source for e in input_data.evidence)
        if is_live and not is_amazon_demo:
            return HypothesisGenerationOutput(
                hypotheses=[],
                rationale="No causal hypothesis could be established from external HTTP telemetry alone."
            )
            
        if is_amazon_demo:
            all_evidence = list(range(len(input_data.evidence)))
            return HypothesisGenerationOutput(
                hypotheses=[
                    HypothesisCandidate(
                        statement="Checkout/API response degradation is being caused by elevated upstream request latency.",
                        reasoning="SIMULATED REASONING",
                        initial_score=0.44,
                        supporting_evidence_indices=all_evidence,
                        predictions=[Prediction(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=30)]
                    ),
                    HypothesisCandidate(
                        statement="Cache behavior is increasing request processing time.",
                        reasoning="SIMULATED REASONING",
                        initial_score=0.31,
                        supporting_evidence_indices=all_evidence,
                        predictions=[Prediction(metric="cache_hit_rate", direction=MetricDirection.INCREASE, threshold_percentage=20)]
                    ),
                    HypothesisCandidate(
                        statement="A recent application change introduced additional request overhead.",
                        reasoning="SIMULATED REASONING",
                        initial_score=0.25,
                        supporting_evidence_indices=all_evidence,
                        predictions=[Prediction(metric="cpu", direction=MetricDirection.DECREASE, threshold_percentage=10)]
                    )
                ],
                rationale="SIMULATED LIVE DEMO"
            )
            
        cache_leads = "cache hit rate measured at 0.15" in text or "cache invalidation" in text
        query_leads = "new product catalog query" in text or "slow queries" in text

        db_score, cache_score, query_score = (0.56, 0.27, 0.17)
        if cache_leads:
            db_score, cache_score, query_score = (0.24, 0.57, 0.19)
        elif query_leads:
            db_score, cache_score, query_score = (0.22, 0.20, 0.58)

        all_evidence = list(range(len(input_data.evidence)))
        return HypothesisGenerationOutput(
            hypotheses=[
                HypothesisCandidate(
                    statement="Database connection pool exhaustion is delaying checkout requests.",
                    initial_score=db_score,
                    supporting_evidence_indices=all_evidence,
                    predictions=[Prediction(
                        metric="db_connections", direction=MetricDirection.DECREASE,
                        threshold_percentage=60,
                        description="A pool reset should sharply lower active database connections.",
                    )],
                    reasoning="Database pressure can directly create wait time and tail latency.",
                ),
                HypothesisCandidate(
                    statement="A cache stampede is driving excess database work.",
                    initial_score=cache_score,
                    supporting_evidence_indices=all_evidence,
                    predictions=[Prediction(
                        metric="cache_hit_rate", direction=MetricDirection.INCREASE,
                        threshold_percentage=100,
                        description="Restoring cache effectiveness should reduce database pressure.",
                    )],
                    reasoning="Reduced cache effectiveness can make database pressure a downstream symptom.",
                ),
                HypothesisCandidate(
                    statement="A deployment introduced a query performance regression.",
                    initial_score=query_score,
                    supporting_evidence_indices=all_evidence,
                    predictions=[Prediction(
                        metric="p95_latency", direction=MetricDirection.DECREASE,
                        threshold_percentage=35,
                        description="Rolling back the change should reduce tail latency.",
                    )],
                    reasoning="Deployment timing and shared database symptoms make a query regression plausible.",
                ),
            ],
            rationale="Three causally distinct explanations are retained to avoid anchoring on correlated metrics.",
        )

    async def critique(self, input_data: CritiqueInput) -> CritiqueOutput:
        statement = input_data.leading_hypothesis.statement.lower()
        if "cache stampede" in statement:
            intervention = "cache_ttl_change"
        elif "query performance" in statement:
            intervention = "deployment_rollback"
        elif "upstream request latency" in statement:
            intervention = "upstream_latency_mitigation"
        else:
            intervention = "connection_pool_reset"
        alternative = next(
            (h.statement for h in input_data.all_hypotheses if h.id != input_data.leading_hypothesis.id),
            "An alternative explanation remains possible.",
        )
        return CritiqueOutput(
            hypothesis_id=input_data.leading_hypothesis.id,
            objections=["Correlation between database pressure and latency is not proof of the initiating fault."],
            assumptions_identified=["The observed database pressure is causal rather than downstream."],
            evidence_weaknesses=["Initial telemetry is a snapshot and lacks an intervention result."],
            contradictions=[],
            alternative_explanations=[alternative],
            falsification_criteria=[
                "If the targeted intervention does not produce the predicted metric change under held request load, weaken this hypothesis."
            ],
            recommended_experiment_description=(
                f"Apply {intervention} only in the Digital Twin while holding request rate constant."
            ),
            recommended_intervention_type=intervention,
        )

    async def design(self, input_data: ExperimentDesignInput) -> ExperimentDesignOutput:
        statement = input_data.target_hypothesis.statement.lower()
        intervention = input_data.critique.recommended_intervention_type
        if "cache stampede" in statement:
            conditions = [
                MetricExpectation(metric="cache_hit_rate", direction=MetricDirection.INCREASE, threshold_percentage=200),
                MetricExpectation(metric="db_utilization", direction=MetricDirection.DECREASE, threshold_percentage=30),
            ]
            target, params = "redis-cache", {"ttl_seconds": 300}
        elif "query performance" in statement:
            conditions = [
                MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=35),
                MetricExpectation(metric="db_utilization", direction=MetricDirection.DECREASE, threshold_percentage=30),
            ]
            target, params = "checkout-service", {"target_version": "previous_stable"}
        elif "upstream request latency" in statement:
            conditions = [
                MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=30),
                MetricExpectation(metric="error_rate", direction=MetricDirection.DECREASE, threshold_percentage=25),
            ]
            target, params = "upstream-service", {}
            intervention = "upstream_latency_mitigation"
        else:
            conditions = [
                MetricExpectation(metric="db_connections", direction=MetricDirection.DECREASE, threshold_percentage=60),
                MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=45),
            ]
            target, params = "postgresql", {}

        return ExperimentDesignOutput(
            target_hypothesis_id=input_data.target_hypothesis.id,
            intervention=InterventionSpec(type=intervention, target=target, parameters=params),
            controls=ExperimentControls(
                request_rate=input_data.current_telemetry.get("request_rate"),
                application_version="current",
            ),
            expected_conditions=conditions,
            observation_window_seconds=10,
            failure_conditions=["Any expected metric condition fails."],
            rationale="The controlled intervention tests a causal prediction rather than an observed correlation.",
        )

    async def generate_remediation(self, input_data: RemediationInput) -> RemediationOutput:
        statement = input_data.verified_hypothesis.statement.lower()
        if "cache stampede" in statement:
            return RemediationOutput(
                type=RemediationType.CONFIG_CHANGE,
                title="Stagger cache expiry and restore a bounded TTL",
                description="Apply a controlled cache TTL policy to prevent a synchronized refill burst.",
                config_change={"cache_ttl_change": {"ttl_seconds": 300}},
                verification_steps=["Replay the incident in the Digital Twin", "Confirm cache hit rate and DB utilization recover"],
                expected_metric_improvements=["Cache hit rate rises", "Database utilization falls"],
            )
        if "query performance" in statement:
            return RemediationOutput(
                type=RemediationType.ROLLBACK,
                title="Roll back the query regression deployment",
                description="Restore the previous stable checkout deployment while the query change is corrected.",
                config_change={"target_version": "previous_stable"},
                verification_steps=["Replay the incident after rollback", "Confirm latency and DB utilization recover"],
                expected_metric_improvements=["P95 latency falls", "Queue pressure reduces"],
            )
        if "upstream request latency" in statement:
            return RemediationOutput(
                type=RemediationType.CONFIG_CHANGE,
                title="Reduce upstream dependency timeout amplification and restore bounded request deadlines.",
                description="SIMULATED REMEDIATION PREVIEW. This will enforce strict timeout limits on upstream dependency calls to prevent thread exhaustion.",
                config_change={"upstream_timeout_ms": 1500, "retry_limit": 1},
                verification_steps=["Replay the incident in the Digital Twin", "Confirm P95 latency and error rate recover"],
                expected_metric_improvements=["P95 latency decreases", "Error rate normalizes"],
            )
        return RemediationOutput(
            type=RemediationType.CODE_PATCH,
            title="Close checkout database sessions on every request path",
            description="Ensure the checkout connection lifecycle returns every acquired session to the pool.",
            diff=(
                "--- a/checkout/db.py\n+++ b/checkout/db.py\n@@\n"
                "- session = pool.acquire()\n"
                "+ async with pool.acquire() as session:\n"
                "+     await execute_checkout(session)\n"
            ),
            verification_steps=["Replay the incident in the Digital Twin", "Confirm pool pressure and tail latency recover"],
            expected_metric_improvements=["Active DB connections fall", "P95 latency falls"],
        )

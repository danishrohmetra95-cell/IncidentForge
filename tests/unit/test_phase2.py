"""Phase 2 tests — comprehensive coverage for all Phase 2 requirements."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from packages.contracts.domain import (
    AgentRun,
    ConditionResult,
    Critique,
    Evidence,
    EvidenceType,
    Experiment,
    ExperimentControls,
    Hypothesis,
    HypothesisStatus,
    Incident,
    IncidentFingerprint,
    IncidentMemoryRecord,
    InterventionSpec,
    InvestigationState,
    MetricDirection,
    MetricExpectation,
    Observation,
    Remediation,
    RemediationType,
    Severity,
    Symptom,
    TelemetrySnapshot,
    VerificationOutcome,
    VerificationResult,
    now,
)
from packages.contracts.agent_io import (
    HypothesisCandidate,
    HypothesisGenerationInput,
    HypothesisGenerationOutput,
    ExperimentDesignInput,
    ExperimentDesignOutput,
    CritiqueInput,
    CritiqueOutput,
)
from packages.reasoning.belief import BeliefUpdateEngine
from packages.reasoning.verification import VerificationEngine
from packages.memory.store import IncidentMemoryStore
from packages.memory.fingerprint import IncidentFingerprinter
from apps.api.persistence.repository import IncidentRepository
from packages.orchestration.orchestrator import (
    InvestigationOrchestrator,
    InvestigationContext,
    MAX_HYPOTHESIS_CYCLES,
    MAX_EXPERIMENT_ATTEMPTS,
    MAX_REMEDIATION_RETRIES,
)
from packages.reasoning.safety import SafetyValidator
from packages.experiments.engine import ExperimentEngine
from packages.simulator.interventions import InterventionRegistry
from packages.simulator.scenarios import load_scenario, create_twin_from_scenario
from packages.agents.deterministic import DeterministicScenarioAgents
from packages.llm.structured import StructuredOutputParser, output_validation_status


def _snapshot(**overrides) -> TelemetrySnapshot:
    defaults = {
        "request_rate": 1000.0, "p50_latency": 50.0, "p95_latency": 100.0,
        "p99_latency": 140.0, "error_rate": 0.1, "db_connections": 80.0,
        "db_utilization": 0.8, "cache_hit_rate": 0.5, "cpu": 0.7,
        "memory": 0.4, "queue_depth": 20.0,
    }
    defaults.update(overrides)
    return TelemetrySnapshot(**defaults)


def _experiment(conditions, intervention=None):
    return Experiment(
        incident_id="inc_test",
        target_hypothesis="hyp_test",
        intervention=intervention or InterventionSpec(type="connection_pool_reset", target="postgresql"),
        controls=ExperimentControls(request_rate=1000),
        expected_conditions=conditions,
    )


# ═══════════════════════════════════════════════════════════════════
# 1. STABLE threshold regression tests
# ═══════════════════════════════════════════════════════════════════

class TestStableThresholdRegression:
    """Verify the verification engine uses the configured threshold_percentage
    for STABLE conditions, not a hardcoded threshold."""

    def test_stable_passes_when_change_below_threshold(self):
        """STABLE condition passes when metric change is below threshold."""
        engine = VerificationEngine()
        exp = _experiment([
            MetricExpectation(
                metric="cpu",
                direction=MetricDirection.STABLE,
                threshold_percentage=10.0,
            ),
        ])
        # cpu: 0.7 -> 0.72 = +2.86% change, which is < 10%
        result = engine.evaluate(exp, _snapshot(), _snapshot(cpu=0.72))
        assert result.outcome == VerificationOutcome.VERIFIED
        assert result.conditions[0].passed is True

    def test_stable_fails_when_change_exceeds_threshold(self):
        """STABLE condition fails when metric change exceeds threshold."""
        engine = VerificationEngine()
        exp = _experiment([
            MetricExpectation(
                metric="cpu",
                direction=MetricDirection.STABLE,
                threshold_percentage=5.0,
            ),
        ])
        # cpu: 0.7 -> 0.8 = +14.3% change, which is >= 5%
        result = engine.evaluate(exp, _snapshot(), _snapshot(cpu=0.8))
        assert result.conditions[0].passed is False

    def test_stable_uses_configured_threshold_not_hardcoded(self):
        """Different threshold_percentage values produce different PASS/FAIL."""
        engine = VerificationEngine()
        # Same metric change: cpu 0.7 -> 0.75 = +7.14% change
        baseline = _snapshot()
        post = _snapshot(cpu=0.75)

        # With threshold 5% → FAIL (7.14% >= 5%)
        exp_strict = _experiment([
            MetricExpectation(metric="cpu", direction=MetricDirection.STABLE, threshold_percentage=5.0),
        ])
        result_strict = engine.evaluate(exp_strict, baseline, post)
        assert result_strict.conditions[0].passed is False

        # With threshold 10% → PASS (7.14% < 10%)
        exp_lenient = _experiment([
            MetricExpectation(metric="cpu", direction=MetricDirection.STABLE, threshold_percentage=10.0),
        ])
        result_lenient = engine.evaluate(exp_lenient, baseline, post)
        assert result_lenient.conditions[0].passed is True


# ═══════════════════════════════════════════════════════════════════
# 2. Historical-memory bonus tests
# ═══════════════════════════════════════════════════════════════════

class TestHistoricalMemoryBonus:
    """Historical matches influence scoring but do NOT automatically determine root cause."""

    def test_historical_match_increases_score(self):
        """A hypothesis with a historical match gets a bonus."""
        engine = BeliefUpdateEngine()
        h1 = Hypothesis(incident_id="inc", statement="DB pool exhaustion", score=0.5)
        h2 = Hypothesis(incident_id="inc", statement="Cache stampede", score=0.5)

        # h1 has a historical match, h2 doesn't
        scores = engine.update(
            [h1, h2], [], [], [],
            historical_matches={h1.id: True, h2.id: False},
        )
        assert scores[h1.id] > scores[h2.id]

    def test_historical_match_does_not_override_experiment(self):
        """A verified experiment for h2 should still outweigh historical bonus for h1."""
        engine = BeliefUpdateEngine()
        h1 = Hypothesis(incident_id="inc", statement="DB pool exhaustion", score=0.5)
        h2 = Hypothesis(incident_id="inc", statement="Cache stampede", score=0.5)

        exp = Experiment(
            incident_id="inc", target_hypothesis=h2.id,
            intervention=InterventionSpec(type="cache_ttl_change", target="redis-cache", parameters={"ttl_seconds": 300}),
            controls=ExperimentControls(),
            expected_conditions=[MetricExpectation(metric="cache_hit_rate", direction=MetricDirection.INCREASE, threshold_percentage=50)],
        )
        verification = VerificationResult(
            experiment_id=exp.id, outcome=VerificationOutcome.VERIFIED,
            conditions=[], passed_count=1, failed_count=0, explanation="pass",
        )

        scores = engine.update(
            [h1, h2], [verification], [], [exp],
            historical_matches={h1.id: True, h2.id: False},
        )
        # h2 verified experiment (+0.35) should outweigh h1 historical bonus (+0.05)
        assert scores[h2.id] > scores[h1.id]

    def test_scoring_is_deterministic(self):
        """Same inputs always produce same outputs."""
        engine = BeliefUpdateEngine()
        h1 = Hypothesis(incident_id="inc", statement="A", score=0.5)
        h2 = Hypothesis(incident_id="inc", statement="B", score=0.3)

        matches = {h1.id: True, h2.id: False}
        s1 = engine.update([h1, h2], [], [], [], historical_matches=matches)
        s2 = engine.update([h1, h2], [], [], [], historical_matches=matches)
        assert s1 == s2


# ═══════════════════════════════════════════════════════════════════
# 3. AgentRun output_validation_status tests
# ═══════════════════════════════════════════════════════════════════

class TestAgentRunOutputValidationStatus:
    """output_validation_status field exists and is populated end-to-end."""

    def test_field_exists_on_domain_model(self):
        run = AgentRun(agent="test", model="test", incident_id="inc", status="running")
        assert hasattr(run, "output_validation_status")
        assert run.output_validation_status is None

    def test_field_can_be_set(self):
        run = AgentRun(agent="test", model="test", incident_id="inc", status="completed")
        run.output_validation_status = "validated"
        assert run.output_validation_status == "validated"

        run.output_validation_status = "repaired"
        assert run.output_validation_status == "repaired"

        run.output_validation_status = "failed"
        assert run.output_validation_status == "failed"

    def test_repaired_structured_output_is_classified_as_repaired(self):
        parser = StructuredOutputParser()
        parser.parse(
            "{'hypothesis_id': 'hyp_test', 'objections': [], 'assumptions_identified': [], "
            "'evidence_weaknesses': [], 'contradictions': [], "
            "'alternative_explanations': [], 'falsification_criteria': [], "
            "'recommended_experiment_description': 'test', "
            "'recommended_intervention_type': 'connection_pool_reset'}",
            CritiqueOutput,
        )
        assert output_validation_status.get() == "repaired"

    @pytest.mark.asyncio
    async def test_populated_during_orchestrator_run(self):
        """After a full orchestrator run, agent runs have output_validation_status."""
        scenario = load_scenario('incident-001-db-pool')
        incident = Incident(
            title=scenario["title"],
            description=scenario["description"],
            severity=Severity(scenario["severity"]),
            service=scenario["service"],
        )
        agents = DeterministicScenarioAgents()
        registry = InterventionRegistry()
        orchestrator = InvestigationOrchestrator(
            triage_agent=agents, evidence_analyst=agents,
            hypothesis_engine=agents, adversarial_critic=agents,
            experiment_designer=agents, remediation_agent=agents,
            experiment_engine=ExperimentEngine(registry),
            verification_engine=VerificationEngine(),
            belief_engine=BeliefUpdateEngine(),
            safety_validator=SafetyValidator(registry),
            twin_factory=lambda s: create_twin_from_scenario(s),
            memory_store=IncidentMemoryStore(),
            fingerprinter=IncidentFingerprinter(),
        )
        ctx = await orchestrator.run(incident, scenario)

        assert len(ctx.agent_runs) > 0
        for run in ctx.agent_runs:
            assert run.output_validation_status is not None, f"Agent run {run.agent} missing output_validation_status"
            assert run.output_validation_status in ("validated", "repaired", "failed")


# ═══════════════════════════════════════════════════════════════════
# 4. Hypothesis challenge endpoint tests
# ═══════════════════════════════════════════════════════════════════

class TestHypothesisChallengeEndpoint:
    """POST /api/hypotheses/{id}/challenge executes real critique logic."""

    @pytest.mark.asyncio
    async def test_challenge_produces_real_critique(self):
        from fastapi.testclient import TestClient
        from apps.api.main import app

        client = TestClient(app)

        # First create a demo incident to have hypotheses
        created = client.post("/api/incidents/demo")
        assert created.status_code == 200
        incident_id = created.json()["id"]

        # Wait for investigation to complete
        import time
        time.sleep(0.5)

        # Get the incident to find hypothesis IDs
        inc = client.get(f"/api/incidents/{incident_id}")
        assert inc.status_code == 200
        body = inc.json()
        assert "hypotheses" in body and len(body["hypotheses"]) > 0
        hyp_id = body["hypotheses"][0]["id"]

        # Challenge the hypothesis
        resp = client.post(f"/api/hypotheses/{hyp_id}/challenge")
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "challenged"
        assert result["hypothesis_id"] == hyp_id
        assert "critique" in result
        critique = result["critique"]
        assert len(critique["objections"]) > 0
        assert len(critique["falsification_criteria"]) > 0
        assert critique["recommended_experiment"] != ""

        repo = __import__("apps.api.persistence.repository", fromlist=["get_repository"]).get_repository()
        persisted = await repo.get_critiques(incident_id)
        assert any(item.id == critique["id"] for item in persisted)

    def test_challenge_404_for_unknown_hypothesis(self):
        from fastapi.testclient import TestClient
        from apps.api.main import app

        client = TestClient(app)
        resp = client.post("/api/hypotheses/nonexistent/challenge")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# 5. Hypothesis experiment-design endpoint tests
# ═══════════════════════════════════════════════════════════════════

class TestHypothesisExperimentDesignEndpoint:
    """POST /api/hypotheses/{id}/experiments produces real experiment designs."""

    @pytest.mark.asyncio
    async def test_experiment_design_produces_real_experiment(self):
        from fastapi.testclient import TestClient
        from apps.api.main import app

        client = TestClient(app)

        created = client.post("/api/incidents/demo")
        assert created.status_code == 200
        incident_id = created.json()["id"]

        import time
        time.sleep(0.5)

        inc = client.get(f"/api/incidents/{incident_id}")
        body = inc.json()
        hyp_id = body["hypotheses"][0]["id"]

        resp = client.post(f"/api/hypotheses/{hyp_id}/experiments")
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "designed"
        assert result["hypothesis_id"] == hyp_id
        assert "experiment" in result
        exp = result["experiment"]
        assert exp["target_hypothesis"] == hyp_id
        assert "intervention" in exp
        assert "expected_conditions" in exp
        assert len(exp["expected_conditions"]) > 0
        assert "safety_approved" in result

    def test_experiment_design_404_for_unknown_hypothesis(self):
        from fastapi.testclient import TestClient
        from apps.api.main import app

        client = TestClient(app)
        resp = client.post("/api/hypotheses/nonexistent/experiments")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# 6. Remediation retry tests
# ═══════════════════════════════════════════════════════════════════

class TestRemediationRetry:
    """Bounded retry logic for remediation validation."""

    @pytest.fixture
    def setup_orchestrator(self):
        scenario = load_scenario('incident-001-db-pool')
        incident = Incident(
            title=scenario["title"],
            description=scenario["description"],
            severity=Severity(scenario["severity"]),
            service=scenario["service"],
        )
        agents = DeterministicScenarioAgents()
        registry = InterventionRegistry()
        orchestrator = InvestigationOrchestrator(
            triage_agent=agents, evidence_analyst=agents,
            hypothesis_engine=agents, adversarial_critic=agents,
            experiment_designer=agents, remediation_agent=agents,
            experiment_engine=ExperimentEngine(registry),
            verification_engine=VerificationEngine(),
            belief_engine=BeliefUpdateEngine(),
            safety_validator=SafetyValidator(registry),
            twin_factory=lambda s: create_twin_from_scenario(s),
            memory_store=IncidentMemoryStore(),
            fingerprinter=IncidentFingerprinter(),
        )
        return orchestrator, incident, scenario

    def test_retry_count_is_bounded(self):
        """MAX_REMEDIATION_RETRIES is defined and finite."""
        assert MAX_REMEDIATION_RETRIES >= 1
        assert MAX_REMEDIATION_RETRIES <= 10  # sanity upper bound

    @pytest.mark.asyncio
    async def test_successful_remediation_resolves(self, setup_orchestrator):
        """Normal remediation succeeds and resolves the incident."""
        orchestrator, incident, scenario = setup_orchestrator
        ctx = await orchestrator.run(incident, scenario)
        assert ctx.incident.status == InvestigationState.RESOLVED
        assert ctx.remediation is not None
        assert ctx.remediation.validation_status == "validated"

    @pytest.mark.asyncio
    async def test_every_remediation_attempt_is_recorded(self, setup_orchestrator):
        """Even a successful first-attempt remediation records timeline events."""
        orchestrator, incident, scenario = setup_orchestrator
        ctx = await orchestrator.run(incident, scenario)
        # There should be remediation timeline events
        rem_events = [t for t in ctx.timeline if "remediation" in t.event_type]
        assert len(rem_events) >= 1

    @pytest.mark.asyncio
    async def test_exhausted_retries_produce_failed_state(self, setup_orchestrator):
        """If all remediation attempts fail, investigation transitions to FAILED."""
        orchestrator, incident, scenario = setup_orchestrator

        # Monkey-patch _validate_remediation to always return False
        original_validate = orchestrator._validate_remediation
        orchestrator._validate_remediation = lambda ctx, scenario, rem: False

        ctx = await orchestrator.run(incident, scenario)
        assert ctx.incident.status == InvestigationState.FAILED
        # Timeline should record multiple failed validation attempts
        failed_events = [t for t in ctx.timeline if "remediation.validation_failed" in t.event_type]
        assert len(failed_events) == MAX_REMEDIATION_RETRIES

    @pytest.mark.asyncio
    async def test_no_infinite_loop_on_remediation(self, setup_orchestrator):
        """Even with perpetual validation failure, the investigation terminates."""
        orchestrator, incident, scenario = setup_orchestrator
        orchestrator._validate_remediation = lambda ctx, scenario, rem: False

        ctx = await orchestrator.run(incident, scenario)
        # Investigation must terminate (not hang)
        assert ctx.incident.status == InvestigationState.FAILED


# ═══════════════════════════════════════════════════════════════════
# 7. Repository → memory store integration tests
# ═══════════════════════════════════════════════════════════════════

class TestRepositoryMemoryIntegration:
    """repository.find_similar_memories() delegates to shared memory store."""

    @pytest.mark.asyncio
    async def test_find_similar_with_structural_fallback(self):
        """When embeddings are unavailable, structural similarity is used."""
        repo = IncidentRepository()
        fp = IncidentFingerprint(
            services=["checkout-service"],
            metric_patterns=["p95_latency", "error_rate"],
            symptoms=["High latency"]
        )
        mem = IncidentMemoryRecord(
            incident_id="inc_hist_1",
            fingerprint=fp,
            root_cause="DB pool exhaustion",
            experiment_summary="Tested pool reset",
            verified_intervention="connection_pool_reset",
            remediation_summary="Fixed pool lifecycle"
        )
        await repo.save_memory(mem)

        search_fp = IncidentFingerprint(
            services=["checkout-service"],
            metric_patterns=["p95_latency", "error_rate"],
            symptoms=["High latency"]
        )
        results = await repo.find_similar_memories(search_fp, limit=5)
        assert len(results) > 0
        assert results[0].incident_id == "inc_hist_1"

    @pytest.mark.asyncio
    async def test_find_similar_returns_empty_for_unrelated(self):
        """No matches for completely unrelated fingerprints."""
        repo = IncidentRepository()
        fp = IncidentFingerprint(
            services=["billing-service"],
            metric_patterns=["payment_errors"],
            symptoms=["Payment timeouts"]
        )
        mem = IncidentMemoryRecord(
            incident_id="inc_unrelated",
            fingerprint=fp,
            root_cause="Payment gateway down",
            experiment_summary="Tested gateway",
            verified_intervention="gateway_restart",
            remediation_summary="Restarted gateway"
        )
        await repo.save_memory(mem)

        search_fp = IncidentFingerprint(
            services=["auth-service"],
            metric_patterns=["login_failures"],
            symptoms=["Auth errors"]
        )
        results = await repo.find_similar_memories(search_fp, limit=5)
        # Unrelated services/metrics/symptoms should not match above threshold
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_actual_memories_returned_not_empty(self):
        """When fallback can work, actual matching memories are returned."""
        repo = IncidentRepository()
        # Store multiple memories
        for i in range(3):
            fp = IncidentFingerprint(
                services=["api-gateway"],
                metric_patterns=["latency"],
                symptoms=["slow responses"]
            )
            mem = IncidentMemoryRecord(
                incident_id=f"inc_{i}",
                fingerprint=fp,
                root_cause=f"Cause {i}",
                experiment_summary=f"Exp {i}",
                verified_intervention=f"Fix {i}",
                remediation_summary=f"Rem {i}"
            )
            await repo.save_memory(mem)

        search_fp = IncidentFingerprint(
            services=["api-gateway"],
            metric_patterns=["latency"],
            symptoms=["slow responses"]
        )
        results = await repo.find_similar_memories(search_fp, limit=10)
        assert len(results) == 3


# ═══════════════════════════════════════════════════════════════════
# 8. Failed investigation context persistence tests
# ═══════════════════════════════════════════════════════════════════

class TestFailedInvestigationContextPersistence:
    """When an investigation fails, the FULL context is preserved."""

    @pytest.mark.asyncio
    async def test_failed_investigation_preserves_full_context(self):
        """After a failed investigation, all collected artifacts are accessible."""
        scenario = load_scenario('incident-001-db-pool')
        incident = Incident(
            title=scenario["title"],
            description=scenario["description"],
            severity=Severity(scenario["severity"]),
            service=scenario["service"],
        )
        agents = DeterministicScenarioAgents()
        registry = InterventionRegistry()

        # Force all hypotheses to be bad → guaranteed failure
        async def bad_hypotheses(input_data):
            return HypothesisGenerationOutput(
                hypotheses=[
                    HypothesisCandidate(
                        statement="A cache stampede is driving excess database work.",
                        initial_score=0.99,
                        supporting_evidence_indices=[],
                        predictions=[],
                        reasoning=""
                    )
                ],
                rationale=""
            )
        agents.generate_hypotheses = bad_hypotheses

        orchestrator = InvestigationOrchestrator(
            triage_agent=agents, evidence_analyst=agents,
            hypothesis_engine=agents, adversarial_critic=agents,
            experiment_designer=agents, remediation_agent=agents,
            experiment_engine=ExperimentEngine(registry),
            verification_engine=VerificationEngine(),
            belief_engine=BeliefUpdateEngine(),
            safety_validator=SafetyValidator(registry),
            twin_factory=lambda s: create_twin_from_scenario(s),
            memory_store=IncidentMemoryStore(),
            fingerprinter=IncidentFingerprinter(),
        )
        ctx = await orchestrator.run(incident, scenario)

        # Investigation failed
        assert ctx.incident.status == InvestigationState.FAILED

        # But ALL accumulated context is preserved
        assert len(ctx.evidence) > 0, "Evidence should be preserved"
        assert len(ctx.hypotheses) > 0, "Hypotheses should be preserved"
        assert len(ctx.experiments) > 0, "Experiments should be preserved"
        assert len(ctx.timeline) > 0, "Timeline should be preserved"
        assert len(ctx.agent_runs) > 0, "Agent runs should be preserved"
        assert ctx.hypothesis_cycles == MAX_HYPOTHESIS_CYCLES

    @pytest.mark.asyncio
    async def test_failed_context_retrievable_after_persistence(self):
        """Failed investigation context can be saved and retrieved from repository."""
        scenario = load_scenario('incident-001-db-pool')
        incident = Incident(
            title=scenario["title"],
            description=scenario["description"],
            severity=Severity(scenario["severity"]),
            service=scenario["service"],
        )
        agents = DeterministicScenarioAgents()
        registry = InterventionRegistry()

        # Force failure
        async def bad_hypotheses(input_data):
            return HypothesisGenerationOutput(
                hypotheses=[
                    HypothesisCandidate(
                        statement="A cache stampede is driving excess database work.",
                        initial_score=0.99,
                        supporting_evidence_indices=[],
                        predictions=[],
                        reasoning=""
                    )
                ],
                rationale=""
            )
        agents.generate_hypotheses = bad_hypotheses

        orchestrator = InvestigationOrchestrator(
            triage_agent=agents, evidence_analyst=agents,
            hypothesis_engine=agents, adversarial_critic=agents,
            experiment_designer=agents, remediation_agent=agents,
            experiment_engine=ExperimentEngine(registry),
            verification_engine=VerificationEngine(),
            belief_engine=BeliefUpdateEngine(),
            safety_validator=SafetyValidator(registry),
            twin_factory=lambda s: create_twin_from_scenario(s),
            memory_store=IncidentMemoryStore(),
            fingerprinter=IncidentFingerprinter(),
        )
        ctx = await orchestrator.run(incident, scenario)
        assert ctx.incident.status == InvestigationState.FAILED

        # Save to repository
        repo = IncidentRepository()
        await repo.save_context(ctx)

        # Retrieve and verify full context
        saved_incident = await repo.get_incident(ctx.incident.id)
        assert saved_incident is not None
        assert saved_incident.status == InvestigationState.FAILED

        saved_evidence = await repo.get_evidence(ctx.incident.id)
        assert len(saved_evidence) > 0

        saved_hypotheses = await repo.get_hypotheses(ctx.incident.id)
        assert len(saved_hypotheses) > 0

        saved_experiments = await repo.get_experiments(ctx.incident.id)
        assert len(saved_experiments) > 0

        saved_timeline = await repo.get_timeline(ctx.incident.id)
        assert len(saved_timeline) > 0

        # Failure information is in the timeline
        fail_events = [t for t in saved_timeline if t.event_type == "investigation.failed"]
        assert len(fail_events) > 0

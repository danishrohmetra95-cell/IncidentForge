from packages.contracts.domain import (
    Evidence,
    Experiment,
    ExperimentControls,
    Hypothesis,
    InterventionSpec,
    MetricDirection,
    MetricExpectation,
    Observation,
    TelemetrySnapshot,
    VerificationOutcome,
    VerificationResult,
)
from packages.reasoning.belief import BeliefUpdateEngine
from packages.reasoning.verification import VerificationEngine

def test_belief_supporting_evidence_increases_belief() -> None:
    h1 = Hypothesis(incident_id="inc", statement="H1", score=0.5, supporting_evidence=["ev1"])
    h2 = Hypothesis(incident_id="inc", statement="H2", score=0.5)
    ev1 = Evidence(incident_id="inc", type="LOG", source="app", observation="error", strength=0.8, id="ev1")
    
    scores = BeliefUpdateEngine().update([h1, h2], [], [ev1], [])
    assert scores[h1.id] > scores[h2.id]
    assert round(sum(scores.values()), 3) == 1.0

def test_belief_contradictory_evidence_decreases_belief() -> None:
    h1 = Hypothesis(incident_id="inc", statement="H1", score=0.5, contradicting_evidence=["ev1"])
    h2 = Hypothesis(incident_id="inc", statement="H2", score=0.5)
    ev1 = Evidence(incident_id="inc", type="LOG", source="app", observation="error", strength=0.8, id="ev1")
    
    scores = BeliefUpdateEngine().update([h1, h2], [], [ev1], [])
    assert scores[h1.id] < scores[h2.id]
    assert round(sum(scores.values()), 3) == 1.0

def test_belief_scores_remain_normalized() -> None:
    # A complex case where multiple modifiers apply
    h1 = Hypothesis(incident_id="inc", statement="H1", score=0.1, supporting_evidence=["ev1"])
    h2 = Hypothesis(incident_id="inc", statement="H2", score=0.8, contradicting_evidence=["ev2"])
    h3 = Hypothesis(incident_id="inc", statement="H3", score=0.1)
    ev1 = Evidence(incident_id="inc", type="LOG", source="app", observation="err", strength=1.0, id="ev1")
    ev2 = Evidence(incident_id="inc", type="METRIC", source="db", observation="high cpu", strength=1.0, id="ev2")
    
    scores = BeliefUpdateEngine().update([h1, h2, h3], [], [ev1, ev2], [])
    assert round(sum(scores.values()), 3) == 1.0


def test_verification_majority_conditions_fail() -> None:
    engine = VerificationEngine()
    experiment = Experiment(
        incident_id="inc", target_hypothesis="h1",
        intervention=InterventionSpec(type="test", target="test"),
        expected_conditions=[
            MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=20),
            MetricExpectation(metric="error_rate", direction=MetricDirection.DECREASE, threshold_percentage=20),
            MetricExpectation(metric="cpu", direction=MetricDirection.DECREASE, threshold_percentage=20),
        ]
    )
    baseline = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=100, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    post = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=50, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    
    # 1 passes (latency), 2 fail (error_rate, cpu don't decrease)
    result = engine.evaluate(experiment, baseline, post)
    assert result.outcome == VerificationOutcome.REJECTED

def test_verification_majority_conditions_pass() -> None:
    engine = VerificationEngine()
    experiment = Experiment(
        incident_id="inc", target_hypothesis="h1",
        intervention=InterventionSpec(type="test", target="test"),
        expected_conditions=[
            MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=20),
            MetricExpectation(metric="error_rate", direction=MetricDirection.DECREASE, threshold_percentage=20),
        ]
    )
    baseline = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=100, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    post = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=50, p99_latency=200, error_rate=0.01, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    
    # Both pass
    result = engine.evaluate(experiment, baseline, post)
    assert result.outcome == VerificationOutcome.VERIFIED

def test_verification_stable_direction() -> None:
    engine = VerificationEngine()
    experiment = Experiment(
        incident_id="inc", target_hypothesis="h1",
        intervention=InterventionSpec(type="test", target="test"),
        expected_conditions=[
            MetricExpectation(metric="p95_latency", direction=MetricDirection.STABLE, threshold_percentage=5),
        ]
    )
    baseline = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=100, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    
    # Change is exactly 4% (passes)
    post1 = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=104, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    assert engine.evaluate(experiment, baseline, post1).outcome == VerificationOutcome.VERIFIED

    # Change is exactly 5% (fails because < threshold is required)
    post2 = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=105, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    assert engine.evaluate(experiment, baseline, post2).outcome == VerificationOutcome.REJECTED

def test_verification_exactly_at_threshold_decrease() -> None:
    engine = VerificationEngine()
    experiment = Experiment(
        incident_id="inc", target_hypothesis="h1",
        intervention=InterventionSpec(type="test", target="test"),
        expected_conditions=[
            MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=20),
        ]
    )
    baseline = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=100, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    # Exactly -20%
    post = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=80, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    assert engine.evaluate(experiment, baseline, post).outcome == VerificationOutcome.VERIFIED

def test_verification_zero_baseline() -> None:
    engine = VerificationEngine()
    experiment = Experiment(
        incident_id="inc", target_hypothesis="h1",
        intervention=InterventionSpec(type="test", target="test"),
        expected_conditions=[
            MetricExpectation(metric="error_rate", direction=MetricDirection.INCREASE, threshold_percentage=10),
        ]
    )
    baseline = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=100, p99_latency=200, error_rate=0.0, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    post = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=100, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    
    # Engine uses pct_change = 0.0 if baseline == 0
    # pct_change >= 10 will fail since 0 >= 10 is false
    assert engine.evaluate(experiment, baseline, post).outcome == VerificationOutcome.REJECTED

def test_verification_unexpected_metric() -> None:
    engine = VerificationEngine()
    experiment = Experiment(
        incident_id="inc", target_hypothesis="h1",
        intervention=InterventionSpec(type="test", target="test"),
        expected_conditions=[
            MetricExpectation(metric="non_existent", direction=MetricDirection.INCREASE, threshold_percentage=10),
        ]
    )
    baseline = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=100, p99_latency=200, error_rate=0.0, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    post = TelemetrySnapshot(request_rate=100, p50_latency=50, p95_latency=100, p99_latency=200, error_rate=0.05, db_connections=10, db_utilization=0.5, cpu=0.8, cache_hit_rate=0.9, memory=1024, queue_depth=5)
    
    # Missing metric defaults to 0.0 for both base and post. pct_change = 0.0. INCREASE fails.
    assert engine.evaluate(experiment, baseline, post).outcome == VerificationOutcome.REJECTED

def test_memory_changing_symptoms_changes_fingerprint() -> None:
    from packages.memory.fingerprint import IncidentFingerprinter
    from packages.contracts.domain import Incident, Severity, Symptom, MetricDirection
    
    incident = Incident(title="Test", description="Test", severity=Severity.SEV_2, service="test")
    sym1 = Symptom(name="cpu", metric="cpu", direction=MetricDirection.INCREASE, observed_value=90.0, normal_range="40")
    sym2 = Symptom(name="mem", metric="mem", direction=MetricDirection.INCREASE, observed_value=90.0, normal_range="40")
    
    fingerprinter = IncidentFingerprinter()
    fp1 = fingerprinter.fingerprint(incident, [sym1], [])
    fp2 = fingerprinter.fingerprint(incident, [sym2], [])
    
    assert fp1.symptoms != fp2.symptoms
    assert fp1 != fp2

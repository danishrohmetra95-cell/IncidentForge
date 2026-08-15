from packages.contracts.domain import (
    Experiment,
    ExperimentControls,
    InterventionSpec,
    MetricDirection,
    MetricExpectation,
    TelemetrySnapshot,
    VerificationOutcome,
)
from packages.reasoning.safety import SafetyValidator
from packages.reasoning.verification import VerificationEngine
from packages.simulator.interventions import InterventionRegistry


def snapshot(**changes: float) -> TelemetrySnapshot:
    values = {
        "request_rate": 1000.0, "p50_latency": 50.0, "p95_latency": 100.0,
        "p99_latency": 140.0, "error_rate": 0.1, "db_connections": 80.0,
        "db_utilization": 0.8, "cache_hit_rate": 0.5, "cpu": 0.7,
        "memory": 0.4, "queue_depth": 20.0,
    }
    values.update(changes)
    return TelemetrySnapshot(**values)


def experiment(conditions: list[MetricExpectation], intervention: InterventionSpec | None = None) -> Experiment:
    return Experiment(
        incident_id="inc_test",
        target_hypothesis="hyp_test",
        intervention=intervention or InterventionSpec(type="connection_pool_reset", target="postgresql"),
        controls=ExperimentControls(request_rate=1000),
        expected_conditions=conditions,
    )


def test_safety_rejects_unregistered_and_out_of_bounds_actions() -> None:
    validator = SafetyValidator(InterventionRegistry())
    unsafe = experiment(
        [MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=20)],
        InterventionSpec(type="shell_exec", target="host", parameters={"command": "rm -rf /"}),
    )
    approved, reasons = validator.validate(unsafe)
    assert not approved
    assert "not registered" in reasons[0]

    invalid_ttl = experiment(
        [MetricExpectation(metric="cache_hit_rate", direction=MetricDirection.INCREASE, threshold_percentage=10)],
        InterventionSpec(type="cache_ttl_change", target="redis-cache", parameters={"ttl_seconds": 0}),
    )
    approved, reasons = validator.validate(invalid_ttl)
    assert not approved
    assert "ttl_seconds" in reasons[0]


def test_verification_requires_every_condition_to_pass() -> None:
    engine = VerificationEngine()
    full = experiment([
        MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=50),
        MetricExpectation(metric="error_rate", direction=MetricDirection.DECREASE, threshold_percentage=50),
    ])
    verified = engine.evaluate(full, snapshot(), snapshot(p95_latency=40, error_rate=0.02))
    assert verified.outcome == VerificationOutcome.VERIFIED

    mixed = experiment([
        MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=50),
        MetricExpectation(metric="cache_hit_rate", direction=MetricDirection.INCREASE, threshold_percentage=50),
    ])
    inconclusive = engine.evaluate(mixed, snapshot(), snapshot(p95_latency=40, cache_hit_rate=0.55))
    assert inconclusive.outcome == VerificationOutcome.INCONCLUSIVE
    assert inconclusive.passed_count == 1

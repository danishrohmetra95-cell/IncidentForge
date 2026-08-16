from packages.contracts.domain import (
    Experiment,
    ExperimentControls,
    Hypothesis,
    InterventionSpec,
    MetricDirection,
    MetricExpectation,
    VerificationOutcome,
    VerificationResult,
)
from packages.reasoning.belief import BeliefUpdateEngine


def test_verified_experiment_updates_only_target_hypothesis() -> None:
    target = Hypothesis(incident_id="inc", statement="target", score=0.5)
    alternative = Hypothesis(incident_id="inc", statement="alternative", score=0.5)
    experiment = Experiment(
        incident_id="inc", target_hypothesis=target.id,
        intervention=InterventionSpec(type="connection_pool_reset", target="postgresql"),
        controls=ExperimentControls(),
        expected_conditions=[MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=20)],
    )
    result = VerificationResult(
        experiment_id=experiment.id, outcome=VerificationOutcome.VERIFIED,
        conditions=[], passed_count=1, failed_count=0, explanation="pass",
    )

    scores = BeliefUpdateEngine().update([target, alternative], [result], [], [experiment])
    assert scores[target.id] > scores[alternative.id]
    assert round(sum(scores.values()), 3) == 1.0


def test_rejected_experiment_penalizes_target_hypothesis() -> None:
    target = Hypothesis(incident_id="inc", statement="target", score=0.5)
    alternative = Hypothesis(incident_id="inc", statement="alternative", score=0.5)
    experiment = Experiment(
        incident_id="inc", target_hypothesis=target.id,
        intervention=InterventionSpec(type="connection_pool_reset", target="postgresql"),
        controls=ExperimentControls(),
        expected_conditions=[MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=20)],
    )
    result = VerificationResult(
        experiment_id=experiment.id, outcome=VerificationOutcome.REJECTED,
        conditions=[], passed_count=0, failed_count=1, explanation="fail",
    )

    scores = BeliefUpdateEngine().update([target, alternative], [result], [], [experiment])
    assert scores[target.id] < scores[alternative.id]
    assert round(sum(scores.values()), 3) == 1.0


def test_inconclusive_experiment_does_not_drastically_change_target() -> None:
    target = Hypothesis(incident_id="inc", statement="target", score=0.5)
    alternative = Hypothesis(incident_id="inc", statement="alternative", score=0.5)
    experiment = Experiment(
        incident_id="inc", target_hypothesis=target.id,
        intervention=InterventionSpec(type="connection_pool_reset", target="postgresql"),
        controls=ExperimentControls(),
        expected_conditions=[MetricExpectation(metric="p95_latency", direction=MetricDirection.DECREASE, threshold_percentage=20)],
    )
    result = VerificationResult(
        experiment_id=experiment.id, outcome=VerificationOutcome.INCONCLUSIVE,
        conditions=[], passed_count=1, failed_count=1, explanation="mixed",
    )

    scores = BeliefUpdateEngine().update([target, alternative], [result], [], [experiment])
    # INCONCLUSIVE has 0 effect in BeliefUpdateEngine currently.
    # We just ensure it doesn't arbitrarily hurt or help more than the alternative.
    assert scores[target.id] == scores[alternative.id]
    assert round(sum(scores.values()), 3) == 1.0

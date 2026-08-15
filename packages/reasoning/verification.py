"""Deterministic verification engine.

NO LLM involvement. Purely rule-based evaluation of experiment outcomes.
Receives experiment expectations, baseline, and post-intervention telemetry.
Returns VERIFIED, REJECTED, or INCONCLUSIVE with full audit trail.
"""

from packages.contracts.domain import (
    ConditionResult,
    Experiment,
    MetricDirection,
    TelemetrySnapshot,
    VerificationOutcome,
    VerificationResult,
)


class VerificationEngine:
    """Evaluates experiment results against predicted conditions.

    Rules:
      VERIFIED     — all conditions pass
      REJECTED     — majority of conditions fail
      INCONCLUSIVE — mixed results
    """

    def evaluate(
        self,
        experiment: Experiment,
        baseline: TelemetrySnapshot,
        post: TelemetrySnapshot,
    ) -> VerificationResult:
        conditions: list[ConditionResult] = []

        for expectation in experiment.expected_conditions:
            metric = expectation.metric
            base_val = self._get_metric(baseline, metric)
            post_val = self._get_metric(post, metric)

            if base_val == 0:
                pct_change = 0.0
            else:
                pct_change = ((post_val - base_val) / abs(base_val)) * 100.0

            threshold = expectation.threshold_percentage
            direction = expectation.direction

            if direction == MetricDirection.DECREASE:
                passed = pct_change <= -threshold
                expected_desc = f"decrease >= {threshold}%"
            elif direction == MetricDirection.INCREASE:
                passed = pct_change >= threshold
                expected_desc = f"increase >= {threshold}%"
            else:  # STABLE
                passed = abs(pct_change) < threshold
                expected_desc = f"change < {threshold}%"

            detail = (
                f"{metric}: baseline={base_val:.2f}, post={post_val:.2f}, "
                f"change={pct_change:+.1f}%, expected {expected_desc} → "
                f"{'PASS' if passed else 'FAIL'}"
            )

            conditions.append(ConditionResult(
                metric=metric,
                expected=expected_desc,
                observed_value=post_val,
                baseline_value=base_val,
                passed=passed,
                detail=detail,
            ))

        passed_count = sum(1 for c in conditions if c.passed)
        failed_count = len(conditions) - passed_count
        total = len(conditions)

        if total == 0:
            outcome = VerificationOutcome.INCONCLUSIVE
            explanation = "No expected conditions defined."
        elif passed_count == total:
            outcome = VerificationOutcome.VERIFIED
            explanation = f"All {total} conditions passed."
        elif failed_count > total / 2:
            outcome = VerificationOutcome.REJECTED
            explanation = f"{failed_count}/{total} conditions failed — hypothesis rejected."
        else:
            outcome = VerificationOutcome.INCONCLUSIVE
            explanation = f"{passed_count}/{total} conditions passed — result inconclusive."

        return VerificationResult(
            experiment_id=experiment.id,
            outcome=outcome,
            conditions=conditions,
            passed_count=passed_count,
            failed_count=failed_count,
            explanation=explanation,
        )

    @staticmethod
    def _get_metric(snapshot: TelemetrySnapshot, metric: str) -> float:
        """Extract a metric value from a telemetry snapshot by name."""
        metric_map = {
            "p50_latency": snapshot.p50_latency,
            "p95_latency": snapshot.p95_latency,
            "p99_latency": snapshot.p99_latency,
            "error_rate": snapshot.error_rate,
            "db_connections": snapshot.db_connections,
            "db_utilization": snapshot.db_utilization,
            "cache_hit_rate": snapshot.cache_hit_rate,
            "cpu": snapshot.cpu,
            "memory": snapshot.memory,
            "queue_depth": snapshot.queue_depth,
            "request_rate": snapshot.request_rate,
        }
        return metric_map.get(metric, 0.0)

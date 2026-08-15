"""Counterfactual engine — "What if we had intervened earlier?"

Runs a replay of the incident with an earlier intervention point
and compares cumulative failures. Results are clearly labeled as
simulated counterfactual analysis, not historical data.
"""

from packages.contracts.domain import CounterfactualResult
from packages.simulator.twin import DigitalTwin


class CounterfactualEngine:

    def replay(
        self,
        twin: DigitalTwin,
        intervention_type: str,
        intervention_params: dict,
        total_ticks: int = 30,
        early_intervention_tick: int = 5,
        error_request_multiplier: float = 1000.0,
    ) -> CounterfactualResult:
        """Compare actual outcome vs earlier intervention.

        1. Clone the twin at fault-injected state
        2. Run full simulation WITHOUT intervention → count failures
        3. Clone again, apply intervention earlier → count failures
        4. Return comparison
        """
        # Actual scenario: no intervention
        actual_twin = twin.clone()
        actual_failures = 0
        for tick in range(total_ticks):
            actual_twin.tick(steps=1)
            snapshot = actual_twin.observe()
            actual_failures += int(snapshot.error_rate * error_request_multiplier)

        # Counterfactual: intervene at early_intervention_tick
        cf_twin = twin.clone()
        cf_failures = 0
        for tick in range(total_ticks):
            if tick == early_intervention_tick:
                cf_twin.apply_intervention(intervention_type, intervention_params)
            cf_twin.tick(steps=1)
            snapshot = cf_twin.observe()
            cf_failures += int(snapshot.error_rate * error_request_multiplier)

        avoided = max(0, actual_failures - cf_failures)

        return CounterfactualResult(
            scenario_label=f"Counterfactual: {intervention_type} at tick {early_intervention_tick}",
            actual_failed_requests=actual_failures,
            counterfactual_failed_requests=cf_failures,
            estimated_avoided_failures=avoided,
            intervention_time_offset_seconds=early_intervention_tick,
            note="Simulated counterfactual analysis — not historical data.",
        )

"""Experiment engine — orchestrates the experiment lifecycle.

design → validate → execute → observe → verify

The engine captures baseline telemetry, runs the intervention on
the Digital Twin, captures post-intervention telemetry, and feeds
results to the deterministic verification engine.
"""

from packages.contracts.domain import (
    Experiment,
    Observation,
    TelemetrySnapshot,
    VerificationResult,
)
from packages.simulator.twin import DigitalTwin
from packages.simulator.interventions import InterventionRegistry
from packages.reasoning.verification import VerificationEngine
from packages.reasoning.safety import SafetyValidator


class ExperimentEngine:

    def __init__(self, registry: InterventionRegistry | None = None):
        self._registry = registry or InterventionRegistry()
        self._safety = SafetyValidator(self._registry)
        self._verification = VerificationEngine()

    def available_interventions(self) -> list[str]:
        return list(self._registry.registered)

    def run(
        self,
        experiment: Experiment,
        twin: DigitalTwin,
    ) -> tuple[Observation, VerificationResult]:
        """Execute an experiment on the Digital Twin and verify results.

        1. Capture baseline
        2. Apply intervention
        3. Run simulation for observation window
        4. Capture post-intervention
        5. Verify against expected conditions
        """
        # Capture baseline before intervention
        baseline = twin.observe()

        # Apply intervention via registry (security boundary)
        self._registry.execute(
            twin,
            experiment.intervention.type,
            experiment.intervention.parameters,
        )

        # Run simulation for observation window
        twin.tick(steps=experiment.observation_window_seconds)

        # Capture post-intervention state
        post_intervention = twin.observe()

        # Collect snapshots
        snapshots = [baseline, post_intervention]

        observation = Observation(
            experiment_id=experiment.id,
            baseline=baseline,
            post_intervention=post_intervention,
            duration_seconds=float(experiment.observation_window_seconds),
            raw_snapshots=snapshots,
        )

        # Deterministic verification
        verification = self._verification.evaluate(
            experiment, baseline, post_intervention
        )

        return observation, verification

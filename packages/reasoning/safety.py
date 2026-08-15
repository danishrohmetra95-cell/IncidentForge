"""Safety validator — gate between AI experiment proposals and Digital Twin execution.

The LLM cannot execute arbitrary actions. Only registered interventions
are executable, and all parameters must be within bounds.
"""

from packages.contracts.domain import Experiment
from packages.simulator.interventions import InterventionRegistry


class SafetyValidator:
    """Validates experiments before they reach the Digital Twin.

    Pipeline:
      schema validation → registry check → target validation → parameter bounds → approved/rejected
    """

    def __init__(self, registry: InterventionRegistry):
        self._registry = registry

    def validate(self, experiment: Experiment) -> tuple[bool, list[str]]:
        """Returns (approved, reasons). If not approved, reasons explain why."""
        reasons: list[str] = []

        # 1. Schema validation
        if not experiment.intervention:
            reasons.append("Missing intervention specification.")
            return False, reasons

        if not experiment.intervention.type:
            reasons.append("Missing intervention type.")
            return False, reasons

        # 2–4. Registry, target, and parameter validation. Keeping all
        # intervention-specific bounds in the registry prevents a second,
        # divergent validation vocabulary from emerging here.
        reasons.extend(self._registry.validate(
            experiment.intervention.type,
            experiment.intervention.target,
            experiment.intervention.parameters,
        ))
        if reasons:
            return False, reasons

        # 5. Observation window bounds
        if experiment.observation_window_seconds < 1:
            reasons.append("Observation window must be >= 1 second.")
            return False, reasons
        if experiment.observation_window_seconds > 300:
            reasons.append("Observation window must be <= 300 seconds.")
            return False, reasons

        # 6. Must have at least one expected condition
        if not experiment.expected_conditions:
            reasons.append("Experiment must define at least one expected condition.")
            return False, reasons

        return True, []

"""Registered, bounded interventions for the controlled Digital Twin.

This is the execution security boundary: a model can name an intervention in
an experiment proposal, but it cannot supply a command, a host path, or an
unregistered target. Only these handlers can mutate the simulator.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from packages.contracts.domain import TelemetrySnapshot
from packages.simulator.twin import DigitalTwin


@dataclass(frozen=True)
class InterventionDefinition:
    name: str
    allowed_targets: frozenset[str]
    allowed_parameters: frozenset[str]


class InterventionRegistry:
    _definitions = {
        "connection_pool_reset": InterventionDefinition(
            "connection_pool_reset", frozenset({"postgresql", "db-pool"}), frozenset()
        ),
        "cache_flush": InterventionDefinition(
            "cache_flush", frozenset({"redis-cache"}), frozenset()
        ),
        "cache_ttl_change": InterventionDefinition(
            "cache_ttl_change", frozenset({"redis-cache"}), frozenset({"ttl_seconds"})
        ),
        "deployment_rollback": InterventionDefinition(
            "deployment_rollback", frozenset({"checkout-service"}), frozenset({"target_version"})
        ),
        "feature_flag_disable": InterventionDefinition(
            "feature_flag_disable", frozenset({"checkout-service"}), frozenset({"flag"})
        ),
        "worker_restart": InterventionDefinition(
            "worker_restart", frozenset({"worker-queue"}), frozenset()
        ),
        "upstream_latency_mitigation": InterventionDefinition(
            "upstream_latency_mitigation", frozenset({"upstream-service"}), frozenset()
        ),
    }

    @property
    def registered(self) -> list[str]:
        return list(self._definitions)

    def is_registered(self, intervention_type: str) -> bool:
        return intervention_type in self._definitions

    def validate(self, intervention_type: str, target: str, params: dict[str, Any]) -> list[str]:
        definition = self._definitions.get(intervention_type)
        if not definition:
            return [f"Intervention '{intervention_type}' is not registered."]

        reasons: list[str] = []
        if target not in definition.allowed_targets:
            reasons.append(
                f"Target '{target}' is not allowed for {intervention_type}; "
                f"allowed: {sorted(definition.allowed_targets)}."
            )
        unexpected = set(params) - definition.allowed_parameters
        if unexpected:
            reasons.append(f"Unsupported parameter(s): {', '.join(sorted(unexpected))}.")

        if intervention_type == "cache_ttl_change":
            ttl = params.get("ttl_seconds")
            if not isinstance(ttl, int) or isinstance(ttl, bool) or not 1 <= ttl <= 86400:
                reasons.append("cache_ttl_change requires integer ttl_seconds in [1, 86400].")
        if intervention_type == "feature_flag_disable" and params.get("flag") != "new_checkout_flow":
            reasons.append("feature_flag_disable only permits the registered new_checkout_flow flag.")
        if intervention_type == "deployment_rollback" and params.get("target_version") is not None:
            target_version = params["target_version"]
            if not isinstance(target_version, str) or not target_version.strip():
                reasons.append("target_version must be a non-empty string when provided.")
        return reasons

    def execute(self, twin: DigitalTwin, intervention_type: str, params: dict[str, Any]) -> None:
        definition = self._definitions.get(intervention_type)
        if not definition:
            raise ValueError(f"Intervention '{intervention_type}' is not registered.")
        # Target validation happens in SafetyValidator. Parameter validation is repeated
        # here so no caller can bypass the registry by invoking execute directly.
        reasons = self.validate(intervention_type, next(iter(definition.allowed_targets)), params)
        parameter_reasons = [reason for reason in reasons if not reason.startswith("Target '")]
        if parameter_reasons:
            raise ValueError("; ".join(parameter_reasons))
        twin.apply_intervention(intervention_type, params)

    def observe(self, twin: DigitalTwin) -> TelemetrySnapshot:
        return twin.observe()

    def checkpoint(self, twin: DigitalTwin) -> DigitalTwin:
        """Capture an in-memory checkpoint for a reversible simulation experiment."""
        return twin.clone()

    def rollback(self, twin: DigitalTwin, checkpoint: DigitalTwin) -> None:
        """Restore a checkpoint; this can only affect an in-memory Digital Twin."""
        twin.__dict__.clear()
        twin.__dict__.update(copy.deepcopy(checkpoint.__dict__))

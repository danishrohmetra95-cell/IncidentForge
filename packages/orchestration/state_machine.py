"""Investigation state machine.

Controls legal state transitions during an incident investigation.
Agents cannot arbitrarily skip states.
State changes are emitted as events.
"""

from __future__ import annotations

from packages.contracts.domain import InvestigationState


# Legal transitions: from_state -> set of allowed to_states
TRANSITIONS: dict[InvestigationState, set[InvestigationState]] = {
    InvestigationState.CREATED: {
        InvestigationState.INGESTING,
        InvestigationState.FAILED,
    },
    InvestigationState.INGESTING: {
        InvestigationState.TRIAGING,
        InvestigationState.FAILED,
    },
    InvestigationState.TRIAGING: {
        InvestigationState.EVIDENCE_COLLECTION,
        InvestigationState.FAILED,
    },
    InvestigationState.EVIDENCE_COLLECTION: {
        InvestigationState.HYPOTHESIS_GENERATION,
        InvestigationState.FAILED,
    },
    InvestigationState.HYPOTHESIS_GENERATION: {
        InvestigationState.HYPOTHESIS_CRITIQUE,
        InvestigationState.RESOLVED,
        InvestigationState.FAILED,
    },
    InvestigationState.HYPOTHESIS_CRITIQUE: {
        InvestigationState.EXPERIMENT_DESIGN,
        InvestigationState.FAILED,
    },
    InvestigationState.EXPERIMENT_DESIGN: {
        InvestigationState.EXPERIMENT_VALIDATION,
        InvestigationState.FAILED,
    },
    InvestigationState.EXPERIMENT_VALIDATION: {
        InvestigationState.EXPERIMENT_EXECUTION,
        InvestigationState.EXPERIMENT_DESIGN,     # rejected -> redesign
        InvestigationState.FAILED,
    },
    InvestigationState.EXPERIMENT_EXECUTION: {
        InvestigationState.OBSERVATION,
        InvestigationState.FAILED,
    },
    InvestigationState.OBSERVATION: {
        InvestigationState.BELIEF_UPDATE,
        InvestigationState.FAILED,
    },
    InvestigationState.BELIEF_UPDATE: {
        InvestigationState.REMEDIATION,
        InvestigationState.HYPOTHESIS_GENERATION,  # hypothesis rejected -> re-hypothesize
        InvestigationState.EXPERIMENT_DESIGN,      # inconclusive -> try another experiment
        InvestigationState.FAILED,
    },
    InvestigationState.REMEDIATION: {
        InvestigationState.REMEDIATION_VALIDATION,
        InvestigationState.FAILED,
    },
    InvestigationState.REMEDIATION_VALIDATION: {
        InvestigationState.RESOLVED,
        InvestigationState.REMEDIATION,            # validation failed -> re-remediate
        InvestigationState.FAILED,
    },
    InvestigationState.RESOLVED: set(),            # terminal
    InvestigationState.FAILED: set(),              # terminal
}


class IllegalTransition(Exception):
    def __init__(self, current: InvestigationState, target: InvestigationState):
        self.current = current
        self.target = target
        super().__init__(f"Illegal transition: {current.value} -> {target.value}")


class InvestigationStateMachine:
    """Enforces the investigation lifecycle state transitions."""

    def __init__(self, initial: InvestigationState = InvestigationState.CREATED):
        self._state = initial
        self._history: list[InvestigationState] = [initial]

    @property
    def state(self) -> InvestigationState:
        return self._state

    @property
    def history(self) -> list[InvestigationState]:
        return list(self._history)

    @property
    def is_terminal(self) -> bool:
        return self._state in (InvestigationState.RESOLVED, InvestigationState.FAILED)

    def can_transition(self, target: InvestigationState) -> bool:
        return target in TRANSITIONS.get(self._state, set())

    def transition(self, target: InvestigationState) -> InvestigationState:
        """Transition to target state. Raises IllegalTransition if not allowed."""
        if not self.can_transition(target):
            raise IllegalTransition(self._state, target)
        self._state = target
        self._history.append(target)
        return self._state

    def allowed_transitions(self) -> set[InvestigationState]:
        return TRANSITIONS.get(self._state, set())

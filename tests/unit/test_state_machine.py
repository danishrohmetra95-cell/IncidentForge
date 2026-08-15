import pytest

from packages.contracts.domain import InvestigationState
from packages.orchestration.state_machine import IllegalTransition, InvestigationStateMachine


def test_state_machine_rejects_stage_skips() -> None:
    machine = InvestigationStateMachine()

    with pytest.raises(IllegalTransition):
        machine.transition(InvestigationState.EXPERIMENT_EXECUTION)

    machine.transition(InvestigationState.INGESTING)
    machine.transition(InvestigationState.TRIAGING)
    assert machine.history == [InvestigationState.CREATED, InvestigationState.INGESTING, InvestigationState.TRIAGING]


def test_rejected_experiment_can_only_return_to_design() -> None:
    machine = InvestigationStateMachine(InvestigationState.EXPERIMENT_VALIDATION)
    assert machine.can_transition(InvestigationState.EXPERIMENT_DESIGN)
    assert not machine.can_transition(InvestigationState.REMEDIATION)

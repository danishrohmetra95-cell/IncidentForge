import asyncio

import pytest

from apps.api.services import build_orchestrator
from packages.contracts.domain import Incident, InvestigationState, Severity, VerificationOutcome
from packages.simulator.scenarios import load_scenario


@pytest.mark.parametrize(
    ("scenario_id", "intervention"),
    [
        ("incident-001-db-pool", "connection_pool_reset"),
        ("incident-002-cache-stampede", "cache_ttl_change"),
        ("incident-003-query-regression", "deployment_rollback"),
    ],
)
def test_full_investigation_lifecycle_is_verified_and_resolved(scenario_id: str, intervention: str) -> None:
    scenario = load_scenario(scenario_id)
    incident = Incident(
        title=scenario["title"], description=scenario["description"],
        severity=Severity(scenario["severity"]), service=scenario["service"], scenario_id=scenario_id,
        reasoning_mode="deterministic_demo",
    )
    orchestrator, _ = asyncio.run(build_orchestrator(incident.id))
    context = asyncio.run(orchestrator.run(incident, scenario))

    assert context.state_machine.state == InvestigationState.RESOLVED
    assert len(context.hypotheses) >= 3
    assert context.experiments[-1].intervention.type == intervention
    assert context.verifications[-1].outcome == VerificationOutcome.VERIFIED
    assert context.remediation is not None
    assert context.remediation.validation_status == "validated"

    # Regression check: verified hypothesis must be the highest scoring
    from packages.contracts.domain import HypothesisStatus
    verified_hyp = next(h for h in context.hypotheses if h.status == HypothesisStatus.VERIFIED)
    other_hyps = [h for h in context.hypotheses if h.id != verified_hyp.id]
    for other in other_hyps:
        assert verified_hyp.score > other.score

    # Assert that the resolved confidence does not remain 0.333
    assert verified_hyp.score > 0.333

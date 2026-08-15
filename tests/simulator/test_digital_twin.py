from packages.simulator.scenarios import create_twin_from_scenario, load_scenario
from packages.simulator.interventions import InterventionRegistry


def test_db_pool_scenario_is_deterministic_and_causally_improves() -> None:
    scenario = load_scenario("incident-001-db-pool")
    first = create_twin_from_scenario(scenario)
    second = create_twin_from_scenario(scenario)

    assert first.observe() == second.observe()
    before = first.observe()
    InterventionRegistry().execute(first, "connection_pool_reset", {})
    first.tick(10)
    after = first.observe()

    assert before.p95_latency > 800
    assert after.p95_latency < before.p95_latency * 0.2
    assert after.error_rate < before.error_rate
    assert after.db_connections < before.db_connections


def test_each_primary_intervention_changes_its_intended_cause() -> None:
    registry = InterventionRegistry()
    cases = [
        ("incident-002-cache-stampede", "cache_ttl_change", {"ttl_seconds": 300}, "cache_hit_rate"),
        ("incident-003-query-regression", "deployment_rollback", {"target_version": "previous_stable"}, "p95_latency"),
    ]
    for scenario_id, intervention, params, metric in cases:
        twin = create_twin_from_scenario(load_scenario(scenario_id))
        before = twin.observe()
        registry.execute(twin, intervention, params)
        twin.tick(10)
        after = twin.observe()
        if metric == "cache_hit_rate":
            assert after.cache_hit_rate > before.cache_hit_rate
        else:
            assert after.p95_latency < before.p95_latency

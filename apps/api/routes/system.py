"""System routes — model listing, health, counterfactual."""

from fastapi import APIRouter, HTTPException

from apps.api.persistence.repository import get_repository

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/models")
async def list_models():
    """List available Featherless models."""
    try:
        from apps.api.services import get_gateway
        gw = get_gateway()
        models = await gw.list_models()
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


@router.get("/incidents/{incident_id}/counterfactual")
async def get_counterfactual(incident_id: str):
    """Run counterfactual analysis for a resolved incident."""
    repo = get_repository()
    inc = await repo.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    ctx = repo._contexts.get(incident_id)
    if not ctx or not ctx.experiments:
        raise HTTPException(status_code=400, detail="No experiments to replay")

    # Load scenario data for twin construction
    scenario_data = {}
    if inc.scenario_id:
        from packages.simulator.scenarios import load_scenario
        scenario_data = load_scenario(inc.scenario_id)

    from packages.simulator.scenarios import create_twin_from_scenario
    from packages.experiments.counterfactual import CounterfactualEngine

    twin = create_twin_from_scenario(scenario_data)
    last_exp = ctx.experiments[-1]

    engine = CounterfactualEngine()
    result = engine.replay(
        twin=twin,
        intervention_type=last_exp.intervention.type,
        intervention_params=last_exp.intervention.parameters,
        total_ticks=30,
        early_intervention_tick=5,
    )

    return result.model_dump()

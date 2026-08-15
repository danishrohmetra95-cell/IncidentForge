"""System routes — model listing, health, counterfactual."""

from fastapi import APIRouter, HTTPException

from apps.api.routes.incidents import _incidents, _investigations

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/models")
async def list_models():
    """List available Featherless models."""
    try:
        from packages.llm.gateway import ModelGateway
        gw = ModelGateway()
        models = await gw.list_models()
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


@router.get("/incidents/{incident_id}/counterfactual")
async def get_counterfactual(incident_id: str):
    """Run counterfactual analysis for a resolved incident."""
    if incident_id not in _incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    record = _incidents[incident_id]
    scenario_data = record["scenario_data"]
    ctx = _investigations.get(incident_id)

    if not ctx or not ctx.experiments:
        raise HTTPException(status_code=400, detail="No experiments to replay")

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

"""Experiment and hypothesis challenge routes."""

from fastapi import APIRouter, HTTPException

from apps.api.routes.incidents import _investigations, _get_incident

router = APIRouter(prefix="/api", tags=["experiments"])


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Get experiment details and results."""
    for ctx in _investigations.values():
        for exp in ctx.experiments:
            if exp.id == experiment_id:
                result = {
                    "id": exp.id,
                    "incident_id": exp.incident_id,
                    "target_hypothesis": exp.target_hypothesis,
                    "intervention": exp.intervention.model_dump(),
                    "controls": exp.controls.model_dump(),
                    "expected_conditions": [ec.model_dump() for ec in exp.expected_conditions],
                    "observation_window_seconds": exp.observation_window_seconds,
                    "status": exp.status,
                    "baseline": exp.baseline,
                }

                # Find matching observation and verification
                for obs in ctx.observations:
                    if obs.experiment_id == exp.id:
                        result["observation"] = {
                            "baseline": obs.baseline.model_dump(),
                            "post_intervention": obs.post_intervention.model_dump(),
                            "duration_seconds": obs.duration_seconds,
                        }

                for v in ctx.verifications:
                    if v.experiment_id == exp.id:
                        result["verification"] = {
                            "outcome": v.outcome.value,
                            "conditions": [c.model_dump() for c in v.conditions],
                            "passed_count": v.passed_count,
                            "failed_count": v.failed_count,
                            "explanation": v.explanation,
                        }

                return result

    raise HTTPException(status_code=404, detail="Experiment not found")


@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(experiment_id: str):
    """Get observation and verification results for an experiment."""
    for ctx in _investigations.values():
        for i, exp in enumerate(ctx.experiments):
            if exp.id == experiment_id:
                obs = next((o for o in ctx.observations if o.experiment_id == exp.id), None)
                ver = next((v for v in ctx.verifications if v.experiment_id == exp.id), None)

                return {
                    "experiment_id": experiment_id,
                    "observation": obs.model_dump() if obs else None,
                    "verification": ver.model_dump() if ver else None,
                }

    raise HTTPException(status_code=404, detail="Experiment not found")

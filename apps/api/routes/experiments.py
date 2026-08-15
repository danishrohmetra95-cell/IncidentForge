"""Experiment and hypothesis challenge routes."""

from fastapi import APIRouter, HTTPException

from apps.api.persistence.repository import get_repository
from packages.reasoning.safety import SafetyValidator
from packages.reasoning.verification import VerificationEngine
from packages.simulator.interventions import InterventionRegistry
from packages.simulator.scenarios import load_scenario, create_twin_from_scenario
from packages.experiments.engine import ExperimentEngine

router = APIRouter(prefix="/api", tags=["experiments"])


@router.get("/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    """Get experiment details and results."""
    repo = get_repository()
    for ctx in repo._contexts.values():
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
    repo = get_repository()
    for ctx in repo._contexts.values():
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


@router.post("/experiments/{experiment_id}/validate")
async def validate_experiment(experiment_id: str):
    """Validate an experiment against the safety validator.

    Returns the safety validation result including whether the experiment
    is approved and any rejection reasons.
    """
    repo = get_repository()
    for ctx in repo._contexts.values():
        for exp in ctx.experiments:
            if exp.id == experiment_id:
                registry = InterventionRegistry()
                validator = SafetyValidator(registry)
                approved, reasons = validator.validate(exp)

                exp.status = "validated" if approved else "rejected"
                await repo.save_context(ctx)

                return {
                    "experiment_id": experiment_id,
                    "approved": approved,
                    "reasons": reasons,
                    "status": exp.status,
                }
    raise HTTPException(status_code=404, detail="Experiment not found")


@router.post("/experiments/{experiment_id}/execute")
async def execute_experiment(experiment_id: str):
    """Execute an experiment on the Digital Twin.

    Runs the intervention on a fresh twin, captures baseline and
    post-intervention telemetry, and performs deterministic verification.
    """
    repo = get_repository()
    for ctx in repo._contexts.values():
        for exp in ctx.experiments:
            if exp.id == experiment_id:
                if exp.status not in ("validated", "proposed"):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Experiment status is '{exp.status}', must be 'validated' to execute",
                    )

                # Get incident to load scenario
                inc = await repo.get_incident(exp.incident_id)
                if not inc or not inc.scenario_id:
                    raise HTTPException(status_code=400, detail="No scenario data for experiment")

                scenario_data = load_scenario(inc.scenario_id)
                twin = create_twin_from_scenario(scenario_data)

                # Run the experiment on the twin
                registry = InterventionRegistry()
                engine = ExperimentEngine(registry)
                observation, verification = engine.run(exp, twin)

                exp.status = "completed"
                exp.baseline = {
                    "p95_latency": observation.baseline.p95_latency,
                    "error_rate": observation.baseline.error_rate,
                    "db_utilization": observation.baseline.db_utilization,
                    "cpu": observation.baseline.cpu,
                    "cache_hit_rate": observation.baseline.cache_hit_rate,
                }

                # Store results in context
                ctx.observations.append(observation)
                ctx.verifications.append(verification)
                await repo.save_context(ctx)

                return {
                    "experiment_id": experiment_id,
                    "status": "completed",
                    "observation": {
                        "baseline": observation.baseline.model_dump(),
                        "post_intervention": observation.post_intervention.model_dump(),
                        "duration_seconds": observation.duration_seconds,
                    },
                    "verification": {
                        "outcome": verification.outcome.value,
                        "conditions": [c.model_dump() for c in verification.conditions],
                        "passed_count": verification.passed_count,
                        "failed_count": verification.failed_count,
                        "explanation": verification.explanation,
                    },
                }

    raise HTTPException(status_code=404, detail="Experiment not found")

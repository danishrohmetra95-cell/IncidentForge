"""Remediation routes."""

from fastapi import APIRouter, HTTPException

from apps.api.persistence.repository import get_repository
from packages.simulator.scenarios import load_scenario, create_twin_from_scenario

router = APIRouter(prefix="/api", tags=["remediation"])


@router.get("/incidents/{incident_id}/remediation")
async def get_remediation(incident_id: str):
    repo = get_repository()
    inc = await repo.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    ctx = repo._contexts.get(incident_id)
    if not ctx or not ctx.remediation:
        return None

    rem = ctx.remediation
    return {
        "id": rem.id,
        "incident_id": rem.incident_id,
        "hypothesis_id": rem.hypothesis_id,
        "type": rem.type.value,
        "title": rem.title,
        "description": rem.description,
        "diff": rem.diff,
        "config_change": rem.config_change,
        "validation_status": rem.validation_status,
        "validation_detail": rem.validation_detail,
    }


@router.post("/remediation/{id}/validate")
async def validate_remediation(id: str):
    """Validate remediation by replaying in the Digital Twin.

    Creates a fresh twin with the original fault, applies the verified
    intervention (the one that proved the root cause), runs the simulation,
    and checks whether post-fix metrics are within healthy baselines.
    """
    repo = get_repository()
    for ctx in repo._contexts.values():
        if ctx.remediation and ctx.remediation.id == id:
            rem = ctx.remediation
            inc = await repo.get_incident(rem.incident_id)
            if not inc or not inc.scenario_id:
                raise HTTPException(
                    status_code=400,
                    detail="No scenario data available for remediation replay",
                )

            scenario_data = load_scenario(inc.scenario_id)

            # Find the verified experiment that proved the root cause
            verified_experiment = next(
                (exp for exp in reversed(ctx.experiments)
                 if exp.target_hypothesis == rem.hypothesis_id
                 and exp.status == "completed"),
                None,
            )
            if not verified_experiment:
                raise HTTPException(
                    status_code=400,
                    detail="No completed experiment found for this remediation's hypothesis",
                )

            # Create fresh twin with the original fault
            twin = create_twin_from_scenario(scenario_data)

            # Apply the verified intervention (the fix)
            twin.apply_intervention(
                verified_experiment.intervention.type,
                verified_experiment.intervention.parameters,
            )

            # Run simulation with fix applied
            twin.tick(steps=20)
            post_fix = twin.observe()

            # Check against healthy thresholds
            healthy_p95 = 120.0   # ms
            healthy_error = 0.02  # 2%
            healthy_cpu = 0.40

            checks = {
                "p95_latency": {
                    "value": post_fix.p95_latency,
                    "threshold": healthy_p95 * 3,
                    "passed": post_fix.p95_latency < healthy_p95 * 3,
                },
                "error_rate": {
                    "value": post_fix.error_rate,
                    "threshold": healthy_error * 3,
                    "passed": post_fix.error_rate < healthy_error * 3,
                },
                "cpu": {
                    "value": post_fix.cpu,
                    "threshold": healthy_cpu * 2,
                    "passed": post_fix.cpu < healthy_cpu * 2,
                },
            }

            all_passed = all(c["passed"] for c in checks.values())

            rem.validation_status = "validated" if all_passed else "failed"
            rem.validation_detail = (
                "Post-fix metrics within healthy baseline"
                if all_passed
                else "Post-fix metrics did not meet healthy baseline"
            )

            return {
                "remediation_id": id,
                "validated": all_passed,
                "validation_status": rem.validation_status,
                "validation_detail": rem.validation_detail,
                "post_fix_metrics": post_fix.model_dump(),
                "checks": checks,
            }

    raise HTTPException(status_code=404, detail="Remediation not found")

"""Hypothesis challenge and experiment-design endpoints.

These endpoints invoke the configured adversarial critic / experiment designer
agent (or deterministic fallback) to produce real critiques and experiments.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from apps.api.persistence.repository import get_repository
from packages.contracts.domain import (
    Critique,
    Experiment,
    ExperimentControls,
    Hypothesis,
    InterventionSpec,
    MetricExpectation,
)
from packages.contracts.agent_io import CritiqueInput, CritiqueOutput, ExperimentDesignInput, ExperimentDesignOutput
from apps.api.services import build_orchestrator

router = APIRouter(prefix="/api", tags=["hypotheses"])

@router.post("/hypotheses/{id}/challenge")
async def challenge_hypothesis(id: str):
    """Invoke the adversarial critic to generate a real critique of a hypothesis."""
    repo = get_repository()

    # Find the hypothesis and its context
    ctx = None
    hyp = None
    for c in repo._contexts.values():
        for h in c.hypotheses:
            if h.id == id:
                ctx = c
                hyp = h
                break
        if hyp:
            break

    if not hyp or not ctx:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    # Build the critique input
    critique_input = CritiqueInput(
        incident_id=ctx.incident.id,
        leading_hypothesis=hyp,
        all_hypotheses=ctx.hypotheses,
        evidence=ctx.evidence,
    )

    # Use exactly the configured agent/fallback selected by the composition
    # root, rather than maintaining a second endpoint-only AI pipeline.
    orchestrator, _ = await build_orchestrator(ctx.incident.id)
    critique_output = await orchestrator._critic.critique(critique_input)

    # Persist the critique
    critique = Critique(
        hypothesis_id=hyp.id,
        objections=critique_output.objections,
        assumptions=critique_output.assumptions_identified,
        evidence_weaknesses=critique_output.evidence_weaknesses,
        contradictions=critique_output.contradictions,
        alternatives=critique_output.alternative_explanations,
        falsification_criteria=critique_output.falsification_criteria,
        recommended_experiment=critique_output.recommended_experiment_description,
    )
    ctx.critiques.append(critique)
    await repo.save_context(ctx)

    return {
        "status": "challenged",
        "hypothesis_id": id,
        "critique": critique.model_dump(),
    }


@router.post("/hypotheses/{id}/experiments")
async def design_experiment(id: str):
    """Invoke the experiment designer to generate a real experiment for a hypothesis."""
    repo = get_repository()

    # Find the hypothesis and its context
    ctx = None
    hyp = None
    for c in repo._contexts.values():
        for h in c.hypotheses:
            if h.id == id:
                ctx = c
                hyp = h
                break
        if hyp:
            break

    if not hyp or not ctx:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    # We need a critique to design against; use the latest for this hypothesis
    # or generate one first
    existing_critiques = [cr for cr in ctx.critiques if cr.hypothesis_id == id]
    if existing_critiques:
        latest_critique = existing_critiques[-1]
        # Build a CritiqueOutput from the stored Critique
        critique_output = CritiqueOutput(
            hypothesis_id=latest_critique.hypothesis_id,
            objections=latest_critique.objections,
            assumptions_identified=latest_critique.assumptions,
            evidence_weaknesses=latest_critique.evidence_weaknesses,
            contradictions=latest_critique.contradictions,
            alternative_explanations=latest_critique.alternatives,
            falsification_criteria=latest_critique.falsification_criteria,
            recommended_experiment_description=latest_critique.recommended_experiment,
            recommended_intervention_type=_infer_intervention_type(hyp),
        )
    else:
        # Generate a fresh critique first
        critique_input = CritiqueInput(
            incident_id=ctx.incident.id,
            leading_hypothesis=hyp,
            all_hypotheses=ctx.hypotheses,
            evidence=ctx.evidence,
        )
        orchestrator, _ = await build_orchestrator(ctx.incident.id)
        critique_output = await orchestrator._critic.critique(critique_input)

    # Invoke experiment designer
    orchestrator, _ = await build_orchestrator(ctx.incident.id)
    available = orchestrator._experiment_engine.available_interventions()
    initial_telemetry = {}
    if ctx.observations:
        last_obs = ctx.observations[-1]
        initial_telemetry = last_obs.post_intervention.model_dump()

    design_input = ExperimentDesignInput(
        incident_id=ctx.incident.id,
        target_hypothesis=hyp,
        critique=critique_output,
        available_interventions=available,
        current_telemetry=initial_telemetry,
    )
    design_output = await orchestrator._experiment_designer.design(design_input)

    # Build the experiment domain object
    experiment = Experiment(
        incident_id=ctx.incident.id,
        target_hypothesis=hyp.id,
        intervention=design_output.intervention,
        controls=design_output.controls,
        expected_conditions=design_output.expected_conditions,
        observation_window_seconds=design_output.observation_window_seconds,
        failure_conditions=design_output.failure_conditions,
    )

    # Validate with safety
    approved, reasons = orchestrator._safety.validate(experiment)
    experiment.status = "validated" if approved else "rejected"

    # Persist the experiment
    ctx.experiments.append(experiment)
    await repo.save_context(ctx)

    return {
        "status": "designed",
        "hypothesis_id": id,
        "experiment": experiment.model_dump(),
        "safety_approved": approved,
        "safety_reasons": reasons,
    }


def _infer_intervention_type(hyp: Hypothesis) -> str:
    """Infer intervention type from hypothesis statement for critique construction."""
    statement = hyp.statement.lower()
    if "cache stampede" in statement:
        return "cache_ttl_change"
    elif "query performance" in statement or "deployment" in statement:
        return "deployment_rollback"
    return "connection_pool_reset"

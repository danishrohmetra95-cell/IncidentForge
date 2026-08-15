"""Adversarial critic — the key differentiator.

This agent MUST NOT simply summarize or approve. It must attempt
to falsify the leading hypothesis by identifying assumptions,
weaknesses, contradictions, and recommending experiments that
distinguish competing explanations.

Core instruction: "Do not approve a hypothesis solely because the
evidence is correlated. Attempt to falsify it."
"""

import json
from packages.contracts.domain import ModelRole
from packages.contracts.agent_io import CritiqueInput, CritiqueOutput
from packages.llm.gateway import ModelGateway
from packages.llm.routing import ModelRouter


class AdversarialCritic:
    def __init__(self, gateway: ModelGateway, router: ModelRouter):
        self.gateway = gateway
        self.router = router

    async def critique(self, input_data: CritiqueInput) -> CritiqueOutput:
        model = await self.router.resolve(ModelRole.DEEP_REASONING)

        system_prompt = """ROLE: Adversarial Hypothesis Critic
TASK: Critically evaluate the leading hypothesis. Your goal is to FALSIFY it, not confirm it.

CORE PRINCIPLE: Correlation is not causation. Do not approve a hypothesis solely because the evidence is correlated. Attempt to falsify it.

YOU MUST:
1. Identify unstated assumptions the hypothesis relies on.
2. Identify weaknesses in the supporting evidence (bias, incompleteness, alternative interpretations).
3. Identify contradictions between the hypothesis and available evidence.
4. Produce at least ONE plausible alternative explanation that fits the evidence equally well or better.
5. Specify what observable evidence or condition would definitively FALSIFY the current hypothesis.
6. Recommend a concrete experiment that could distinguish between the leading hypothesis and alternatives.

EXAMPLE CRITIQUE:
"Current hypothesis: DB connection exhaustion.
Objection: High DB utilization may be a downstream symptom, not the root cause. If a cache stampede is driving excess DB queries, connection pressure is a consequence, not a cause.
Alternative: Cache invalidation cascade causing thundering herd to the database.
Falsification: If resetting the DB connection pool does not materially reduce latency under identical request load, DB pool exhaustion should be weakened as a hypothesis.
Recommended experiment: Reset the DB pool and hold request rate constant. If latency drops >50%, DB exhaustion is supported. If latency remains high, look upstream."

OUTPUT CONTRACT: Return valid JSON:
{
  "hypothesis_id": "the ID of the hypothesis being critiqued",
  "objections": ["substantive objection 1", "objection 2"],
  "assumptions_identified": ["assumption 1", "assumption 2"],
  "evidence_weaknesses": ["weakness 1"],
  "contradictions": ["contradiction 1"],
  "alternative_explanations": ["at least one plausible alternative"],
  "falsification_criteria": ["what would falsify this hypothesis"],
  "recommended_experiment_description": "concrete experiment description",
  "recommended_intervention_type": "one of: connection_pool_reset, cache_flush, cache_ttl_change, deployment_rollback, feature_flag_disable, worker_restart"
}"""

        leading = input_data.leading_hypothesis
        alternatives = [
            {"id": h.id, "statement": h.statement, "score": h.score}
            for h in input_data.all_hypotheses
            if h.id != leading.id
        ]
        evidence_summary = [
            {
                "id": e.id,
                "type": e.type.value if hasattr(e.type, 'value') else e.type,
                "observation": e.observation,
                "strength": e.strength,
            }
            for e in input_data.evidence
        ]

        context = {
            "leading_hypothesis": {
                "id": leading.id,
                "statement": leading.statement,
                "score": leading.score,
                "predictions": [p.model_dump() for p in leading.predictions],
                "supporting_evidence_count": len(leading.supporting_evidence),
                "contradicting_evidence_count": len(leading.contradicting_evidence),
            },
            "alternative_hypotheses": alternatives,
            "evidence": evidence_summary,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, indent=2, default=str)},
        ]

        return await self.gateway.structured_generate(
            messages=messages,
            model=model,
            output_schema=CritiqueOutput,
            agent_name="AdversarialCritic",
        )

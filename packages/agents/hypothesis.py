"""Hypothesis engine — generates multiple competing explanations."""

import json
from packages.contracts.domain import ModelRole
from packages.contracts.agent_io import HypothesisGenerationInput, HypothesisGenerationOutput
from packages.llm.gateway import ModelGateway
from packages.llm.routing import ModelRouter


class HypothesisEngine:
    def __init__(self, gateway: ModelGateway, router: ModelRouter):
        self.gateway = gateway
        self.router = router

    async def generate(self, input_data: HypothesisGenerationInput) -> HypothesisGenerationOutput:
        model = await self.router.resolve(ModelRole.DEEP_REASONING)

        system_prompt = """ROLE: Hypothesis Engine
TASK: Generate multiple competing root-cause hypotheses for an incident.

CONSTRAINTS:
- MUST generate >= 3 competing hypotheses when sufficient evidence exists.
- Hypotheses must be genuinely diverse — not variations of the same idea.
- Each hypothesis MUST include predicted observable consequences (predictions).
- Predictions describe what should be measurable if this hypothesis is correct.
- Assign initial confidence scores based on evidence support (0.0 to 1.0).
- Reference specific evidence items by their index in the provided evidence list.
- Include reasoning for each hypothesis.

EXAMPLE HYPOTHESIS TYPES:
- Database connection pool exhaustion
- Cache stampede / cache invalidation cascade
- Query performance regression (deployment-related)
- Network instability / partition
- Resource contention (CPU/memory)
- Configuration drift

OUTPUT CONTRACT: Return valid JSON:
{
  "hypotheses": [
    {
      "statement": "clear one-line hypothesis statement",
      "initial_score": 0.0-1.0,
      "supporting_evidence_indices": [0, 2],
      "contradicting_evidence_indices": [3],
      "predictions": [
        {
          "metric": "p95_latency",
          "direction": "decrease",
          "threshold_percentage": 50.0,
          "description": "If this hypothesis is correct, resetting the connection pool should reduce P95 latency by >50%"
        }
      ],
      "reasoning": "explanation of why this hypothesis fits the evidence"
    }
  ],
  "rationale": "overall reasoning for the hypothesis set"
}"""

        evidence_summary = []
        for i, ev in enumerate(input_data.evidence):
            evidence_summary.append({
                "index": i,
                "type": ev.type.value if hasattr(ev.type, 'value') else ev.type,
                "source": ev.source,
                "observation": ev.observation,
                "strength": ev.strength,
            })

        context = {
            "incident_id": input_data.incident_id,
            "triage_summary": input_data.triage_summary,
            "symptoms": [s.model_dump() for s in input_data.symptoms],
            "evidence": evidence_summary,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, indent=2, default=str)},
        ]

        return await self.gateway.structured_generate(
            messages=messages,
            model=model,
            output_schema=HypothesisGenerationOutput,
            agent_name="HypothesisEngine",
        )

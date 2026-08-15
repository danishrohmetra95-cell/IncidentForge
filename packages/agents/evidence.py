"""Evidence analyst — gathers and correlates evidence with provenance."""

import json
from packages.contracts.domain import ModelRole
from packages.contracts.agent_io import EvidenceAnalysisInput, EvidenceAnalysisOutput
from packages.llm.gateway import ModelGateway
from packages.llm.routing import ModelRouter


class EvidenceAnalyst:
    def __init__(self, gateway: ModelGateway, router: ModelRouter):
        self.gateway = gateway
        self.router = router

    async def analyze(self, input_data: EvidenceAnalysisInput) -> EvidenceAnalysisOutput:
        model = await self.router.resolve(ModelRole.FAST_REASONING)

        system_prompt = """ROLE: Evidence Analyst
TASK: Gather and correlate evidence from available data sources for an incident investigation.

CONSTRAINTS:
- Every evidence item MUST have provenance (source and observation).
- Inspect: logs, metrics, traces, source code, recent commits, deployments, configuration, historical incidents.
- Do NOT dump entire datasets — extract relevant portions.
- Assess evidence strength (0.0 to 1.0) based on reliability and directness.
- Note which hypotheses each evidence item might support or contradict.
- Identify correlations between evidence items.
- Identify gaps where evidence is missing.

OUTPUT CONTRACT: Return valid JSON with these exact fields:
{
  "evidence": [
    {
      "type": "LOG | METRIC | TRACE | CODE | COMMIT | CONFIG | DEPLOYMENT | HISTORICAL_INCIDENT | SIMULATION_RESULT",
      "source": "string — where this evidence came from",
      "observation": "string — what was observed",
      "strength": 0.0-1.0,
      "supports_hypotheses": ["optional hypothesis descriptions"],
      "contradicts_hypotheses": ["optional hypothesis descriptions"]
    }
  ],
  "correlations": ["string descriptions of evidence correlations"],
  "timeline_observations": ["chronological observations"],
  "gaps": ["areas where evidence is missing or insufficient"]
}"""

        context = {
            "incident_id": input_data.incident_id,
            "triage_summary": input_data.triage_summary,
            "symptoms": [s.model_dump() for s in input_data.symptoms],
            "scenario_data": input_data.scenario_data,
            "historical_incidents": input_data.historical_incidents,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, indent=2, default=str)},
        ]

        return await self.gateway.structured_generate(
            messages=messages,
            model=model,
            output_schema=EvidenceAnalysisOutput,
            agent_name="EvidenceAnalyst",
        )

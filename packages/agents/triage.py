"""Triage agent — classifies the incident without declaring a root cause."""

import json
from packages.contracts.domain import ModelRole
from packages.contracts.agent_io import TriageInput, TriageOutput
from packages.llm.gateway import ModelGateway
from packages.llm.routing import ModelRouter


class TriageAgent:
    def __init__(self, gateway: ModelGateway, router: ModelRouter):
        self.gateway = gateway
        self.router = router

    async def analyze(self, input_data: TriageInput) -> TriageOutput:
        model = await self.router.resolve(ModelRole.FAST_REASONING)

        system_prompt = """ROLE: Incident Triage Specialist
TASK: Classify and characterize a software incident. Identify symptoms, affected services, and abnormal metrics.

CONSTRAINTS:
- You MUST NOT declare or suggest a root cause.
- Focus on WHAT is happening, not WHY.
- Identify all observable symptoms from the telemetry.
- Estimate severity based on impact scope and user-facing degradation.

OUTPUT CONTRACT: Return valid JSON with these exact fields:
{
  "incident_type": "string — e.g. 'service_degradation', 'outage', 'latency_spike'",
  "estimated_severity": "SEV_1 | SEV_2 | SEV_3 | SEV_4",
  "affected_services": ["list of service names"],
  "symptoms": [{"name": "string", "metric": "string", "direction": "increase | decrease | stable", "observed_value": number_or_null, "normal_range": "string_or_null"}],
  "abnormal_metrics": ["list of metric names that are outside normal range"],
  "recent_relevant_events": ["list of recent events that may be relevant"],
  "summary": "brief natural-language summary of the incident characteristics"
}"""

        context = {
            "title": input_data.incident_title,
            "description": input_data.incident_description,
            "service": input_data.service,
            "telemetry": input_data.initial_telemetry,
            "recent_events": input_data.recent_events,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, indent=2)},
        ]

        return await self.gateway.structured_generate(
            messages=messages,
            model=model,
            output_schema=TriageOutput,
            agent_name="TriageAgent",
        )

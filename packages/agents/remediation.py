"""Remediation agent — generates structured remediation after verification."""

import json
from packages.contracts.domain import ModelRole
from packages.contracts.agent_io import RemediationInput, RemediationOutput
from packages.llm.gateway import ModelGateway
from packages.llm.routing import ModelRouter


class RemediationAgent:
    def __init__(self, gateway: ModelGateway, router: ModelRouter):
        self.gateway = gateway
        self.router = router

    async def generate(self, input_data: RemediationInput) -> RemediationOutput:
        model = await self.router.resolve(ModelRole.DEEP_REASONING)

        system_prompt = """ROLE: Remediation Engineer
TASK: Generate a concrete remediation for a verified incident root cause.

CONSTRAINTS:
- The root cause has been VERIFIED through experimentation, not guessed.
- Produce a specific, actionable fix — not generic advice.
- For CODE_PATCH type, produce an actual unified diff showing the fix.
- For CONFIG_CHANGE, specify exact configuration key-value changes.
- For ROLLBACK, specify what to roll back and verification steps.
- Include verification steps to confirm the fix works.
- Include expected metric improvements.

OUTPUT CONTRACT: Return valid JSON:
{
  "type": "CODE_PATCH | CONFIG_CHANGE | ROLLBACK | FEATURE_FLAG | RESOURCE_ACTION",
  "title": "short descriptive title",
  "description": "detailed description of the remediation",
  "diff": "unified diff string for code changes (null if not CODE_PATCH)",
  "config_change": {"key": "value"} or null,
  "verification_steps": ["step 1", "step 2"],
  "expected_metric_improvements": ["P95 latency should return to <150ms", "Error rate should drop below 1%"]
}"""

        evidence_summary = [
            {"observation": e.observation, "source": e.source}
            for e in input_data.root_cause_evidence[:5]
        ]

        context = {
            "incident_id": input_data.incident_id,
            "verified_root_cause": input_data.verified_hypothesis.statement,
            "hypothesis_confidence": input_data.verified_hypothesis.score,
            "supporting_evidence": evidence_summary,
            "experiment_summary": input_data.experiment_summary,
            "service": input_data.service,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, indent=2, default=str)},
        ]

        return await self.gateway.structured_generate(
            messages=messages,
            model=model,
            output_schema=RemediationOutput,
            agent_name="RemediationAgent",
        )

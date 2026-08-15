"""Experiment designer — converts critique into strict experiment specification."""

import json
from packages.contracts.domain import ModelRole
from packages.contracts.agent_io import ExperimentDesignInput, ExperimentDesignOutput
from packages.llm.gateway import ModelGateway
from packages.llm.routing import ModelRouter


class ExperimentDesigner:
    def __init__(self, gateway: ModelGateway, router: ModelRouter):
        self.gateway = gateway
        self.router = router

    async def design(self, input_data: ExperimentDesignInput) -> ExperimentDesignOutput:
        model = await self.router.resolve(ModelRole.DEEP_REASONING)

        system_prompt = """ROLE: Experiment Designer
TASK: Design a controlled experiment to test a hypothesis about an incident.

CONSTRAINTS:
- The intervention type MUST be one from the available_interventions list provided.
- The experiment must be capable of distinguishing the target hypothesis from alternatives.
- Specify clear expected conditions with measurable thresholds.
- Define what variables to hold constant (controls).
- The experiment runs in a Digital Twin simulation, not production.

OUTPUT CONTRACT: Return valid JSON:
{
  "target_hypothesis_id": "the hypothesis ID being tested",
  "intervention": {
    "type": "one of the available intervention types",
    "target": "the system component being targeted",
    "parameters": {}
  },
  "controls": {
    "request_rate": 1800,
    "application_version": "current",
    "extra": {}
  },
  "expected_conditions": [
    {
      "metric": "p95_latency",
      "direction": "decrease",
      "threshold_percentage": 50.0,
      "baseline_value": null
    }
  ],
  "observation_window_seconds": 10,
  "failure_conditions": ["conditions that would indicate experiment failure"],
  "rationale": "why this experiment will distinguish the hypothesis from alternatives"
}"""

        critique = input_data.critique
        context = {
            "target_hypothesis": {
                "id": input_data.target_hypothesis.id,
                "statement": input_data.target_hypothesis.statement,
                "score": input_data.target_hypothesis.score,
            },
            "critique": {
                "objections": critique.objections,
                "alternatives": critique.alternative_explanations,
                "falsification_criteria": critique.falsification_criteria,
                "recommended_experiment": critique.recommended_experiment_description,
                "recommended_intervention": critique.recommended_intervention_type,
            },
            "available_interventions": input_data.available_interventions,
            "current_telemetry": input_data.current_telemetry,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, indent=2, default=str)},
        ]

        return await self.gateway.structured_generate(
            messages=messages,
            model=model,
            output_schema=ExperimentDesignOutput,
            agent_name="ExperimentDesigner",
        )

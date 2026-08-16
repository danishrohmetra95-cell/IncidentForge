# Experimental Falsification Pipeline

IncidentForge relies on the scientific method. Instead of trusting an LLM's guess based on symptoms, it forces the AI to prove its hypothesis by designing an experiment, which deterministic software then evaluates.

## 1. Hypothesis Generation
The `HypothesisGenerator` agent reviews evidence and produces competing hypotheses. Each hypothesis must include testable, quantitative predictions (e.g., "If I rollback the deployment, CPU will decrease").

## 2. Adversarial Critique
The `AdversarialCritic` agent challenges the leading hypothesis. It looks for confirmation bias or conflicting telemetry, and recommends the most decisive falsification test.

## 3. Experiment Design
The `ExperimentDesigner` formulates a strict, executable test. It selects a target hypothesis, an intervention (e.g., `cache_ttl_change`), and defines required metric expectations (e.g., `cache_hit_rate` must `INCREASE` by `200%`).

## 4. Safety Validation
The deterministic `SafetyValidator` inspects the design. It blocks unregistered actions, invalid targets, or out-of-bounds parameters. If rejected, the Designer must try again.

## 5. Execution & Observation
The orchestrator captures a baseline `TelemetrySnapshot`. The Digital Twin executes the approved intervention and ticks forward in time. A post-intervention snapshot is captured.

## 6. Deterministic Verification
The `VerificationEngine` (pure Python, zero LLM) mathematically evaluates the metric deltas against the expected thresholds. 
- **`VERIFIED`**: 100% of conditions pass.
- **`REJECTED`**: A majority of conditions fail.
- **`INCONCLUSIVE`**: Partial pass rate.

## 7. Belief Update
The `BeliefUpdateEngine` mathematically adjusts the confidence scores of all active hypotheses.
- **Verified**: Receives a massive +0.35 score bonus.
- **Rejected**: Receives a massive -0.30 penalty.
- **Inconclusive**: No experiment bonus.

Scores are clamped and strictly normalized across all hypotheses so they always sum to 1.0 (100%).

## 8. Remediation Replay
Once a hypothesis reaches decisive confidence via verification, the `RemediationAgent` formulates a permanent fix. To ensure the fix actually solves the problem, it is applied to a fresh Digital Twin. If the golden signals (p95 latency, errors, CPU) return to healthy baselines, the remediation is validated, and the incident is resolved.

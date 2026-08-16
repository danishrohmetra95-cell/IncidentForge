# Investigation State Machine

IncidentForge uses a strict, finite state machine to enforce the lifecycle of an incident investigation. This ensures that AI agents cannot skip critical steps like safety validation or deterministic verification, and prevents the system from wandering or hallucinating out-of-bounds actions.

The orchestrator guarantees that an investigation either successfully resolves, or cleanly fails and halts.

## The 15-State Lifecycle

1. **`CREATED`**: Incident record initialized in the database.
2. **`INGESTING`**: Raw telemetry and alert metadata are loaded.
3. **`TRIAGING`**: `TriageAgent` classifies severity and identifies impacted services.
4. **`EVIDENCE_COLLECTION`**: `EvidenceAnalyst` extracts logs and metrics.
5. **`HYPOTHESIS_GENERATION`**: `HypothesisGenerator` produces competing causal hypotheses.
6. **`HYPOTHESIS_CRITIQUE`**: `AdversarialCritic` challenges leading hypotheses for assumptions.
7. **`EXPERIMENT_DESIGN`**: `ExperimentDesigner` formulates an intervention and expected metrics.
8. **`EXPERIMENT_VALIDATION`**: `SafetyValidator` verifies the experiment against registered constraints.
9. **`EXPERIMENT_EXECUTION`**: The deterministic `DigitalTwin` simulates the intervention.
10. **`OBSERVATION`**: Post-intervention telemetry is collected.
11. **`BELIEF_UPDATE`**: `VerificationEngine` evaluates metrics, and `BeliefUpdateEngine` adjusts confidence scores.
12. **`REMEDIATION`**: `RemediationAgent` formulates a permanent fix for a verified root cause.
13. **`REMEDIATION_VALIDATION`**: The fix is applied to a clean twin and evaluated for recovery.
14. **`RESOLVED`** (Terminal): Fix passed validation; incident memory stored.
15. **`FAILED`** (Terminal): Unrecoverable error, exhaustion of retry limits, or safety violation.

## Valid Transitions

- **Linear Progression**: Under ideal conditions, states transition sequentially from `CREATED` down to `RESOLVED`.
- **Safety Rejection**: If an experiment fails validation in `EXPERIMENT_VALIDATION`, it transitions back to `EXPERIMENT_DESIGN` (up to a retry limit).
- **Inconclusive Experiment**: If an experiment yields partial success without falsifying the hypothesis in `BELIEF_UPDATE`, it transitions back to `EXPERIMENT_DESIGN`.
- **Falsified Hypothesis**: If an experiment yields a majority-fail (`REJECTED`) in `BELIEF_UPDATE`, the hypothesis score drops, and the state loops back to `HYPOTHESIS_GENERATION`.
- **Failed Validation**: If `REMEDIATION_VALIDATION` fails, it loops back to `REMEDIATION` for another attempt.
- **Failure Short-circuit**: Any unhandled exception, or reaching retry limits, immediately transitions the investigation to `FAILED`.

## Bounded Retries

To prevent infinite loops during investigation:
- **`MAX_HYPOTHESIS_CYCLES` = 3**: If 3 successive hypotheses are rejected, the incident transitions to `FAILED` with "NO VERIFIED ROOT CAUSE".
- **`MAX_EXPERIMENT_ATTEMPTS` = 3**: If an experiment is repeatedly inconclusive or safety-rejected, the incident fails.
- **`MAX_REMEDIATION_ATTEMPTS` = 2**: If remediation fixes continually fail validation, the incident fails.

## Terminal States

- **`RESOLVED`**: All golden signals are restored, a root cause is mathematically verified, and the incident is embedded into institutional memory.
- **`FAILED`**: Denotes exhaustion of options or systemic failure. The full context is persisted for human review.

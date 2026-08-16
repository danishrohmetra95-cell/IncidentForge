# Institutional Memory

IncidentForge ensures that the organization learns from every outage. Resolved incidents are converted into semantic and structural memories, allowing the system to instantly recognize recurring fault patterns in future incidents.

## Incident Fingerprint

When an incident is successfully resolved, the `IncidentFingerprinter` generates a composite fingerprint. This fingerprint combines:
- The incident description
- The verified root cause hypothesis
- The structural attributes (service name, exact symptoms, violated thresholds)

## Symptom Contribution and Semantic Similarity

The `IncidentMemoryStore` uses vector embeddings (via `sentence-transformers` and `pgvector`) to map fingerprints into high-dimensional space.
When a new incident arrives:
1. The orchestrator queries the memory store using the new incident's description and extracted symptoms.
2. The store performs a cosine-similarity search.
3. Incidents with highly similar semantic descriptions **and** matching symptom vectors are retrieved.

## Structural Fallback

If the semantic vector search fails to find a high-confidence match, the system falls back to a purely structural search. It looks for past incidents involving the exact same service and exact same telemetry symptom spikes, ensuring reliable retrieval even when descriptions are vague.

## Historical-Memory Bonus

When historical incidents are retrieved, they influence the current investigation. If a retrieved memory matches one of the AI-generated hypotheses for the current incident, the `BeliefUpdateEngine` awards a historical-memory bonus to that hypothesis. 

However, this bonus is strictly bounded. Institutional memory can *influence* the investigation's starting assumptions, but it cannot supersede deterministic experiment verification. An LLM cannot "hallucinate" certainty based purely on a past outage.

## Verified-Memory Rules and Persistence

- **Persistence**: Incident memory, including the verified hypothesis and validated remediation patch, is saved to PostgreSQL using the `pgvector` extension.
- **Rule of Verification**: Only hypotheses that were mathematically verified by an experiment, and incidents that successfully passed remediation validation, are allowed to enter long-term memory. Failed or rejected investigations are persisted for human audit, but do not pollute the semantic memory pool.

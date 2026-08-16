# IncidentForge

**"IncidentForge does not just guess the root cause. It challenges the hypothesis, runs a controlled experiment in a deterministic Digital Twin, verifies the result, and validates the remediation."**

---

## Problem

Incident diagnosis based only on correlation and log inspection is fundamentally uncertain. When outages occur, on-call engineers (and naive AI tools) often jump to conclusions based on surface-level dashboard anomalies, confusing symptoms with root causes. "Metric A spiked right when Metric B dropped, so A caused B" is a dangerous heuristic. This leads to misdirected remediations, extended MTTR, and "fixes" that worsen the outage.

## Solution

IncidentForge treats every incident as a rigid **scientific investigation**. 

1. **Observe**: Ingests telemetry and classifies the severity.
2. **Hypothesize**: Generates multiple, competing causal explanations for the outage.
3. **Challenge**: An adversarial agent critiques the leading hypothesis to prevent confirmation bias.
4. **Experiment**: Designs a falsifiable test with a specific, bounded intervention.
5. **Simulate**: Safely runs the intervention in a deterministic Digital Twin.
6. **Verify**: Pure deterministic software mathematically evaluates the result.
7. **Remediate**: If verified, formulates and validates a fix before generating an institutional memory record.

## Why It Is Different

- **Adversarial Critic**: Actively looks for unstated assumptions and contradictory evidence in LLM-generated hypotheses.
- **Controlled Experiment**: Formulates falsifiable, quantitative metric predictions.
- **Deterministic Verification**: Evaluates experiment outcomes using pure mathematical logic with zero LLM hallucination risk.
- **Remediation Replay**: Validates generated fixes against the Digital Twin to ensure golden signals recover before declaring resolution.
- **Institutional Incident Memory**: Embeds verified fault patterns into semantic memory to instantly recognize recurrences in future incidents.

---

## Architecture

```
         +-------------+
         | User Alert  |
         +------+------+
                |
                v
         +------+------+
         |   Triage    |
         +------+------+
                |
                v
         +------+------+
         |  Evidence   |
         +------+------+
                |
                v
         +------+------+
         | Hypotheses  |
         +------+------+
                |
                v
         +------+------+
         |   Critic    |
         +------+------+
                |
                v
         +------+------+
         | Exp Design  |
         +------+------+
                |
                v
         +------+------+
         | Safety Val  |
         +------+------+
                |
                v
         +------+------+
         |Digital Twin |
         +------+------+
                |
                v
         +------+------+
         | Observation |
         +------+------+
                |
                v
         +------+------+
         | Verifier    |
         +------+------+
                |
                v
         +------+------+
         |Belief Update|
         +------+------+
                |
                v
         +------+------+
         | Remediation |
         +------+------+
                |
                v
         +------+------+
         | Validation  |
         +------+------+
                |
                v
         +------+------+
         |   Memory    |
         +-------------+
```

## Agent Responsibility Table

| Agent / Component | Role | Responsibility |
|---|---|---|
| **TriageAgent** | LLM | Classifies incident severity, extracts impacted services, and identifies anomalous telemetry. Cannot guess root cause. |
| **EvidenceAnalyst** | LLM | Correlates logs, metrics, and trace patterns to establish supporting/contradicting evidence. |
| **HypothesisGenerator** | LLM | Formulates competing causal explanations with explicit quantitative predictions. |
| **AdversarialCritic** | LLM | Challenges the leading hypothesis, identifies confirmation bias, and designs falsification strategies. |
| **ExperimentDesigner** | LLM | Selects sandboxed interventions and specifies precise threshold expectations for the twin. |
| **SafetyValidator** | Deterministic | Blocks unregistered, out-of-bounds, or destructive interventions. |
| **Digital Twin** | Deterministic | Math-based simulation of a microservices stack that ticks forward in time in response to interventions. |
| **VerificationEngine** | Deterministic | Evaluates the Twin's baseline vs post-intervention telemetry against the designer's thresholds. |
| **BeliefUpdateEngine**| Deterministic | Bayesian-inspired engine that normalizes confidence scores (penalizes rejections, rewards verifications). |
| **RemediationAgent** | LLM | Constructs code diffs, configuration patches, or rollback instructions for the verified root cause. |

---

## Technology Stack

- **FastAPI**: Asynchronous Python backend orchestrator.
- **Next.js / React**: React 18 frontend (Incident Command Center).
- **PostgreSQL**: Relational storage for incidents, experiments, and timeline events.
- **pgvector**: Cosine-similarity vector search for institutional memory retrieval.
- **Featherless AI**: Model routing gateway enabling LLM logic.
- **Deterministic Simulation**: Custom mathematical Digital Twin engine modeling causal system drift.
- **SSE (Server-Sent Events)**: Live streaming of state machine events to the frontend.
- **React Flow**: Visualizing the active reasoning graph.
- **Recharts**: Telemetry and counterfactual data visualization.
- **Docker**: Containerization and deployment.

---

## Scenario System

IncidentForge ships with three deterministic fault scenarios designed with deliberate telemetry ambiguity:
1. **`incident-001-db-pool` (Connection Leak)**: Connections leak during checkout, saturating the DB pool. Symptoms: p95 latency spikes, connection pool hits maximum.
2. **`incident-002-cache-stampede` (Cache Stampede)**: Redis cache invalidation causes direct database hits. Symptoms: cache hit rate drops, DB utilization hits 99%, CPU spikes.
3. **`incident-003-query-regression` (Unindexed Query)**: A new deployment introduces a missing DB index. Symptoms: CPU spikes, queue depth grows, connection pool remains stable.

## Experiment Lab

The Experiment Lab is the visual heart of the investigation. As the orchestrator transitions through states, the UI live-updates via SSE:
- **Reasoning Graph**: Visualizes hypotheses, evidence, and critical challenges using React Flow.
- **Telemetry Charts**: Real-time charts via Recharts showing baseline vs post-intervention metrics.
- **Belief Rankings**: Live sorting of hypotheses based on verification outcomes.

## Memory

Resolved incidents are not forgotten. The incident's exact description, verified hypothesis, and structural symptoms are combined into a dense vector embedding. During Triage for future incidents, PostgreSQL `pgvector` retrieves highly similar past incidents, giving the LLM immediate institutional precedent to accelerate root-cause isolation.

---

## Setup

To run IncidentForge locally:

### 1. Backend & Database

Ensure Docker is running, then start the environment:
```bash
docker compose up -d db redis
```

Install Python dependencies (requires Python 3.11+):
```bash
pip install -r requirements.txt
```

Run database migrations:
```bash
cd apps/api
alembic upgrade head
```

Start the API:
```bash
# Still inside apps/api
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend

Open a new terminal and navigate to the web directory:
```bash
cd apps/web
npm install
npm run dev
```

The Command Center is now live at [http://localhost:3000](http://localhost:3000).

---

## Testing

Backend test suite (69 rigorous unit/contract/e2e tests):
```bash
python -m pytest tests/ -v
```

Frontend validation:
```bash
cd apps/web
npm run lint
npm run build
```

---

## Demo Instructions

For an immediate, zero-dependency demonstration of the platform (using deterministic fallback agents if no API key is provided):

1. Open the IncidentForge Command Center (`http://localhost:3000`).
2. Click **"Checkout API Degradation"** to select `incident-001-db-pool`.
3. Click **"Run Deterministic Demo"**.
4. **Watch hypotheses form**: See the system parse evidence and generate competing causal explanations.
5. **Watch the critic challenge**: Observe the Adversarial Critic attack the leading hypothesis for unstated assumptions.
6. **Observe the experiment**: See the Experiment Designer propose an intervention (e.g., connection pool reset).
7. **See verification**: The Digital Twin simulates the intervention, and the Deterministic Verifier strictly evaluates the telemetry change against thresholds.
8. **See belief re-ranking**: The verified hypothesis receives a massive confidence boost, suppressing incorrect alternatives.
9. **See remediation validation**: The Remediation Agent proposes a fix, which is validated mathematically against a fresh Twin.
10. **See incident resolve**: The state transitions to `RESOLVED`, and the incident is embedded into PostgreSQL Memory.

---

## Limitations

- **Digital Twin vs Production**: The Digital Twin uses simplified causal mathematical equations (e.g., latency vs CPU load). Real production environments require hooking the Experiment Engine into real chaos engineering or safe-shadow deployment frameworks.
- **Deterministic Scenarios**: The demo scenarios are hardcoded mathematical fixtures. Live model reasoning relies heavily on the quality of telemetry ingested via API.
- **Event Streaming**: SSE streams are currently memory-backed per-process. Scaling to multiple API instances requires hooking the event bus into Redis Pub/Sub (infrastructure is present but simplistic).
- **Model Dependencies**: High-quality reasoning strictly relies on frontier models (e.g., deep reasoning tier). Weaker models will fail safety validation or fail to parse structured JSON.

---

## Future Work

- Integration with real Chaos Mesh or AWS Fault Injection Simulator for production Twin execution.
- Expansion of the Intervention Registry to include Kubernetes-native auto-scaling actions.
- Multi-agent collaboration via WebSockets for collaborative human-AI debugging.

---

## License

MIT License

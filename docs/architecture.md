# IncidentForge Architecture

IncidentForge is an AI-powered incident response and root-cause analysis system that transforms site reliability engineering (SRE) by treating incident response as an **experimental reasoning problem**. 

Rather than relying on hallucination-prone correlation or unverified LLM narrative summaries, IncidentForge operates under a foundational tenet:

> **"AI proposes. Evidence challenges. Experiments test. Deterministic software verifies."**

```
+-----------------------------------------------------------------------------------+
|                                INCIDENTFORGE CORE                                |
|                                                                                   |
|   +-------------------+      +-------------------+      +---------------------+   |
|   |    AI Agents      | ---> |   Digital Twin    | ---> | Deterministic Rules |   |
|   | Propose Hypotheses|      | Execute Controlled|      | Verify Predictions  |   |
|   | & Design Tests    |      | Interventions     |      | & Update Beliefs    |   |
|   +-------------------+      +-------------------+      +---------------------+   |
+-----------------------------------------------------------------------------------+
```

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Investigation Lifecycle](#investigation-lifecycle)
3. [System Architecture](#system-architecture)
4. [Digital Twin Simulation Engine](#digital-twin-simulation-engine)
5. [Deterministic Verification Engine](#deterministic-verification-engine)
6. [Belief Update System](#belief-update-system)
7. [Agent Pipeline & Model Routing](#agent-pipeline--model-routing)
8. [Investigation State Machine](#investigation-state-machine)
9. [End-to-End Data Flow](#end-to-end-data-flow)
10. [Infrastructure & Deployment](#infrastructure--deployment)
11. [API Layer & Interfaces](#api-layer--interfaces)

---

## Design Principles

IncidentForge is engineered around four core architectural principles:

```mermaid
graph TD
    A[Design Principles] --> B[1. AI Proposes, Deterministic Software Verifies]
    A --> C[2. Hypothesis-Driven Investigation]
    A --> D[3. Experimental Falsification Over Correlation]
    A --> E[4. Institutional Memory]

    B --> B1[LLMs generate ideas; pure rules verify outcomes]
    C --> C1[Multiple competing hypotheses ranked simultaneously]
    D --> D1[Active interventions test causal claims in a sandbox]
    E --> E1[Vector embeddings & structured records inform future incidents]
```

### 1. AI Proposes, Deterministic Software Verifies
Large Language Models (LLMs) excel at creative synthesis, broad semantic search, and generating diverse hypotheses across complex multi-service topologies. However, LLMs are non-deterministic and prone to hallucination. IncidentForge delegates all decision gates, safety checks, metric comparisons, and belief scoring to pure, rule-based deterministic software.

### 2. Hypothesis-Driven Investigation
Incidents are not diagnosed by single-shot prompt queries. Instead, the system formulates multiple competing hypotheses to account for ambiguous telemetry (e.g., distinguishing between a connection leak, a cache stampede, and an unindexed query regression). Hypotheses are maintained in parallel with explicit confidence scores.

### 3. Experimental Falsification Over Correlation
Correlation does not imply causation. A spike in CPU utilization during an outage may be a symptom rather than the cause. IncidentForge uses an adversarial approach: it designs controlled experiments to actively attempt to falsify competing hypotheses against a deterministic Digital Twin before endorsing a remediation plan.

### 4. Institutional Memory
Every verified root cause, validated experiment, and successful remediation patch is fingerprinted, embedded with semantic vectors, and persisted to long-term memory. Future investigations retrieve relevant historical precedents during early triage to accelerate root-cause isolation.

---

## Investigation Lifecycle

The IncidentForge investigation lifecycle follows a strict, state-enforced pipeline from initial anomaly detection through post-fix institutional storage.

```mermaid
flowchart TD
    INC[INCIDENT] --> TRIAGE[TRIAGE]
    TRIAGE --> EV_COLL[EVIDENCE COLLECTION]
    EV_COLL --> HYP_GEN[COMPETING HYPOTHESES]
    HYP_GEN --> ADV_CRIT[ADVERSARIAL CRITIQUE]
    ADV_CRIT --> EXP_DSN[EXPERIMENT DESIGN]
    EXP_DSN --> SFTY_VAL[SAFETY VALIDATION]
    SFTY_VAL -- Rejected --> EXP_DSN
    SFTY_VAL -- Approved --> TWIN_EXEC[DIGITAL TWIN EXECUTION]
    TWIN_EXEC --> OBS[OBSERVATION]
    OBS --> DET_VERIF[DETERMINISTIC VERIFICATION]
    DET_VERIF --> BLF_UPD[BELIEF UPDATE]
    
    BLF_UPD -- Hypothesis Rejected --> HYP_GEN
    BLF_UPD -- Inconclusive --> EXP_DSN
    BLF_UPD -- Hypothesis Verified --> VER_RC[VERIFIED ROOT CAUSE]
    
    VER_RC --> REMED[REMEDIATION]
    REMED --> POST_VAL[POST-FIX VALIDATION]
    POST_VAL -- Validation Failed --> REMED
    POST_VAL -- Passed --> INC_MEM[INCIDENT MEMORY]
    INC_MEM --> RESOLVED[RESOLVED]
```

### Lifecycle Stage Breakdown

| Phase | Responsible Component | Key Operations & Artifacts |
| :--- | :--- | :--- |
| **INCIDENT** | Ingestion / Trigger | Anomaly ingested with raw telemetry snapshots, alert metadata, and system identifiers. |
| **TRIAGE** | `TriageAgent` | Classifies incident type, computes severity (`SEV_1` to `SEV_4`), identifies affected services and initial symptoms. **Does not guess root cause.** |
| **EVIDENCE COLLECTION** | `EvidenceAnalyst` | Extracts logs, metrics, trace patterns, configuration diffs, and deployment records. Assigns evidence strength ($0.0 \dots 1.0$). |
| **COMPETING HYPOTHESES** | `HypothesisGenerator` | Produces $N$ competing causal explanations with specific testable predictions (metric changes and thresholds). |
| **ADVERSARIAL CRITIQUE** | `AdversarialCritic` | Challenges leading hypotheses, identifies unstated assumptions, checks for conflicting evidence, and formulates falsification criteria. |
| **EXPERIMENT DESIGN** | `ExperimentDesigner` | Formulates an executable experiment: selects an intervention, parameters, target component, baseline, and expected metric thresholds. |
| **SAFETY VALIDATION** | `SafetyValidator` | Validates proposed intervention against registered schemas, allowed targets, parameter bounds, and observation window constraints. |
| **DIGITAL TWIN EXECUTION** | `DigitalTwin` / `ExperimentEngine` | Clones system state, executes the bounded intervention in simulation, and ticks the causal equations over the observation window. |
| **OBSERVATION** | `ExperimentEngine` | Captures baseline and post-intervention `TelemetrySnapshot` metrics (latencies, errors, pool utilization, CPU, cache hit rate). |
| **DETERMINISTIC VERIFICATION** | `VerificationEngine` | Compares observed metric deltas against predicted thresholds using pure rule evaluation. Outputs `VERIFIED`, `REJECTED`, or `INCONCLUSIVE`. |
| **BELIEF UPDATE** | `BeliefUpdateEngine` | Updates hypothesis confidence scores using Bayesian-inspired weighting. Normalizes scores across all active candidates. |
| **VERIFIED ROOT CAUSE** | Orchestrator | Promotes the hypothesis surpassing confidence thresholds with passing verification to the authoritative root cause. |
| **REMEDIATION** | `RemediationAgent` | Generates a targeted fix: code patch diff, configuration alteration, feature flag change, or rollback instruction. |
| **POST-FIX VALIDATION** | `DigitalTwin` / Orchestrator | Applies remediation patch to the twin, ticks forward, and verifies return of all golden signals to healthy baselines. |
| **INCIDENT MEMORY** | `IncidentMemoryStore` | Generates fingerprint embedding, pairs symptoms and verified interventions, and persists the incident record for future retrieval. |

---

## System Architecture

IncidentForge is structured as a modular monorepo cleanly separating UI, API routing, orchestration, agent definitions, simulation models, and deterministic reasoning engines.

```
c:\Users\danis\Desktop\IncidentForge\
├── apps/
│   ├── api/                  # FastAPI backend service
│   │   ├── routes/           # REST & SSE route controllers
│   │   ├── main.py           # Application entrypoint & CORS middleware
│   │   ├── services.py       # Shared singleton service registry
│   │   └── config.py         # Environment configuration
│   └── web/                  # Next.js 14 frontend (Incident Command Center)
│       ├── src/app/          # App router pages & layouts
│       ├── src/components/   # React components (Flow, Charts, Metric cards)
│       └── src/lib/          # API client & SSE consumer utilities
├── packages/
│   ├── contracts/            # Pydantic domain models, agent I/O, event schemas
│   ├── simulator/            # Deterministic checkout-service Digital Twin
│   ├── reasoning/            # Rule verification, belief updates, safety validation
│   ├── experiments/          # Experiment execution engine & counterfactual replay
│   ├── agents/               # AI agents & deterministic fallback implementations
│   ├── llm/                  # Featherless AI gateway, model routing, JSON parser
│   ├── orchestration/        # Investigation orchestrator & state machine
│   └── memory/               # Vector embeddings, fingerprinting, incident store
├── database/                 # PostgreSQL & pgvector initialization scripts
├── infra/                    # Deployment manifests & infrastructure configs
└── scenarios/                # Pre-configured incident scenarios (e.g. incident-001)
```

### Monorepo Packages Breakdown

```mermaid
graph TB
    subgraph Frontend["Presentation Layer (apps/web)"]
        UI[Incident Command Center<br/>Next.js 14 + React 18 + Tailwind]
        FlowGraph[Investigation Flow Graph<br/>@xyflow/react]
        Charts[Telemetry & Counterfactual Charts<br/>Recharts]
    end

    subgraph Backend["API & Delivery Layer (apps/api)"]
        API[FastAPI Router Engine]
        SSE[SSE Event Stream Hub]
    end

    subgraph OrchestrationLayer["Orchestration & State (packages/orchestration)"]
        Orchestrator[Investigation Orchestrator]
        StateMachine[State Machine Engine]
    end

    subgraph ReasoningLayer["Deterministic Reasoning (packages/reasoning)"]
        Verifier[Verification Engine]
        Belief[Belief Update Engine]
        Safety[Safety Validator]
    end

    subgraph SimulationLayer["Simulation & Testing (packages/simulator, experiments)"]
        Twin[Digital Twin Engine]
        Interventions[Intervention Registry]
        ExpEngine[Experiment Engine]
        Counterfactual[Counterfactual Engine]
    end

    subgraph AgentLayer["Agent & LLM Subsystem (packages/agents, llm)"]
        Agents[Triage / Hypothesis / Critic / Remediation Agents]
        Gateway[Featherless Model Gateway]
        Router[Dynamic Model Router]
        Fallback[Deterministic Scenario Fallbacks]
    end

    subgraph MemoryLayer["Institutional Memory (packages/memory)"]
        MemoryStore[Incident Memory Store]
        Fingerprinter[Incident Fingerprinter]
        Embeddings[Vector Embeddings]
    end

    UI -->|REST / SSE| API
    API --> Orchestrator
    Orchestrator --> StateMachine
    Orchestrator --> Agents
    Agents --> Gateway
    Gateway --> Router
    Agents -.->|Fallback if no API key| Fallback
    Orchestrator --> ExpEngine
    ExpEngine --> Safety
    ExpEngine --> Interventions
    Interventions --> Twin
    ExpEngine --> Verifier
    Orchestrator --> Belief
    Orchestrator --> Counterfactual
    Orchestrator --> MemoryStore
    MemoryStore --> Fingerprinter
```

---

## Digital Twin Simulation Engine

The Digital Twin (`packages/simulator/twin.py`) is a deterministic, tick-based mathematical simulation of a high-throughput microservices checkout service stack.

```mermaid
graph LR
    subgraph Topology["Simulated Topology"]
        GW[API Gateway] --> CHK[Checkout Service]
        CHK --> PG[(PostgreSQL DB)]
        CHK --> RD[(Redis Cache)]
        CHK --> WQ[Worker Queue]
    end
```

### Telemetry Signals Modeled

The simulation maintains continuous, causally bound telemetry metrics:
- **`request_rate`**: Inbound HTTP requests per second (baseline: 1,500 req/s).
- **`p50_latency`**, **`p95_latency`**, **`p99_latency`**: Millisecond response latencies derived from query cost, pool wait times, and CPU saturation.
- **`error_rate`**: Ratio of failed requests ($0.0 \dots 1.0$) driven by tail-latency timeouts and queue drops.
- **`db_connections`**: Active client connections vs. total pool size (default pool: 100).
- **`db_utilization`**: Relational database compute/IO utilization ($0.0 \dots 1.0$).
- **`cache_hit_rate`**: Redis cache hit ratio ($0.0 \dots 1.0$).
- **`cpu`**: CPU load factor on checkout service nodes ($0.0 \dots 1.0$).
- **`memory`**: Memory utilization fraction.
- **`queue_depth`**: Backlogged tasks in the worker queue.

### Causal Equations & Mathematical Dynamics

The Digital Twin calculates internal mechanics each tick ($t$):

1. **Connection Pressure & Exponential Wait Time**:
   $$\text{db\_pressure} = \frac{\text{active\_connections}}{\text{db\_pool\_size}}$$
   $$\text{wait\_time} = \begin{cases} 150.0 \times \exp\left((\text{db\_pressure} - 0.8) \times 8.0\right), & \text{if } \text{db\_pressure} > 0.8 \\ 0.0, & \text{otherwise} \end{cases}$$

2. **Cache Misses & Database Queries**:
   $$\text{cache\_misses} = \text{request\_rate} \times (1.0 - \text{cache\_hit\_rate})$$
   $$\text{effective\_db\_queries} = (0.3 \times \text{request\_rate}) + (0.8 \times \text{cache\_misses})$$

3. **Database Utilization & Saturation**:
   $$\text{db\_utilization} = \min\left(1.0, \frac{\text{effective\_db\_queries} \times \text{db\_query\_cost\_ms}}{25000.0} + 0.3 \times \text{db\_pressure}\right)$$
   $$\text{db\_saturation\_wait} = \max\left(0.0, (\text{db\_utilization} - 0.75) \times 1600.0\right)$$

4. **CPU Load & Tail Latency**:
   $$\text{cpu} = \min\left(1.0, 0.15 + \frac{\text{effective\_db\_queries}}{12000.0} + \frac{\text{active\_connections}}{500.0} + \text{cpu\_overhead}\right)$$
   $$\text{cpu\_latency} = \begin{cases} (\text{cpu} - 0.7) \times 500.0, & \text{if } \text{cpu} > 0.7 \\ 0.0, & \text{otherwise} \end{cases}$$
   $$\text{p95\_latency} = \text{base\_latency} + \text{query\_latency} + \text{wait\_time} + \text{db\_saturation\_wait} + \text{cpu\_latency}$$

5. **Error Rate Progression**:
   Timeout probabilities accumulate when tail latency crosses thresholds (250ms: +3%, 500ms: +8%, 800ms: +12%, CPU > 95%: +10%).

### Fault Injections

The simulator natively reproduces three distinct, high-impact production failure modes:

| Fault Type | Initial Symptoms | Root Cause Mechanism |
| :--- | :--- | :--- |
| `connection_leak` | p95 latency spikes, connection pool saturates, moderate cache degradation | Leaked database connections fail to return to the pool upon request completion; exponential wait queue triggers HTTP timeouts. |
| `cache_stampede` | Cache hit rate collapses (<20%), DB utilization spikes to 95%+, CPU elevates | Key invalidation or TTL expiry causes massive parallel database queries for hot checkout items. |
| `query_regression` | DB utilization rises, CPU rises, queue depth expands, connection pool stable | Unindexed database join introduced in a new deployment ($v1.8$) escalates average `db_query_cost_ms` from 15ms to 60ms. |

### Registered Safe Interventions

Interventions are strictly sandboxed via `InterventionRegistry` (`packages/simulator/interventions.py`):
- `connection_pool_reset`: Flushes and resets active DB connections to 10% capacity. Clears active connection leak parameters.
- `cache_flush`: Clears cache contents (hit rate drops to 5%) to observe recovery behavior.
- `cache_ttl_change`: Adjusts Redis TTL parameters (`ttl_seconds` $\in [1, 86400]$) to recover stampeded keys.
- `deployment_rollback`: Reverts application binary to specified target version (e.g. `v1.7`).
- `feature_flag_disable`: Toggles registered feature flags (e.g. `new_checkout_flow`).
- `worker_restart`: Clears queue depth and restarts async worker processes.

---

## Deterministic Verification Engine

The Verification Engine (`packages/reasoning/verification.py`) contains **zero LLM logic**. It provides mathematically rigid verification of experiment outcomes.

```mermaid
graph TD
    EXP[Experiment Proposal] --> COND[Condition Evaluator]
    BASE[Baseline Telemetry] --> COND
    POST[Post-Intervention Telemetry] --> COND
    
    COND --> COMP{Evaluate % Delta vs Threshold}
    COMP -->|All conditions pass| V[VERIFIED]
    COMP -->|>50% conditions fail| R[REJECTED]
    COMP -->|Mixed / partial pass| I[INCONCLUSIVE]
```

### Evaluation Protocol

For each predicted `MetricExpectation` in an experiment:
1. Baseline value ($B$) and Post-intervention value ($P$) are extracted from `TelemetrySnapshot`.
2. The percentage change is computed:
   $$\Delta\% = \frac{P - B}{|B|} \times 100.0$$
3. Evaluated against direction and threshold ($T\%$):
   - **`DECREASE`**: Condition passes if $\Delta\% \le -T$
   - **`INCREASE`**: Condition passes if $\Delta\% \ge T$
   - **`STABLE`**: Condition passes if $|\Delta\%| < 5.0\%$

### Decision Rules

- **`VERIFIED`**: $100\%$ of predicted conditions pass ($P_{\text{passed}} == N_{\text{total}}$). Proves the causal hypothesis.
- **`REJECTED`**: A majority of predicted conditions fail ($P_{\text{failed}} > N_{\text{total}} / 2$). Falsifies the hypothesis.
- **`INCONCLUSIVE`**: Partial pass rate without majority failure ($0 < P_{\text{passed}} < N_{\text{total}}$). Triggers experiment redesign.

Every condition produces a granular audit record:
```json
{
  "metric": "p95_latency",
  "expected": "decrease >= 50.0%",
  "baseline_value": 482.4,
  "observed_value": 68.2,
  "passed": true,
  "detail": "p95_latency: baseline=482.40, post=68.20, change=-85.9%, expected decrease >= 50.0% -> PASS"
}
```

---

## Belief Update System

The Belief Update Engine (`packages/reasoning/belief.py`) applies a transparent, Bayesian-inspired formula to score and rank competing hypotheses. No LLM generates confidence numbers.

```mermaid
graph LR
    H[Prior Score H_0] --> CALC[Belief Calculator]
    EV[Supporting Evidence +0.15 * strength] --> CALC
    CONTR[Contradicting Evidence -0.10] --> CALC
    VRF[Verified Experiment +0.35] --> CALC
    REJ[Rejected Experiment -0.30] --> CALC
    
    CALC --> CLAMP[Clamp to 0.01..0.99]
    CLAMP --> NORM[Normalize Sum = 1.0]
    NORM --> OUT[Updated Confidence Scores]
```

### Scoring Weights

$$\text{RawScore}(H) = S_{\text{prior}} + \sum_{e \in \text{Support}} (0.15 \times \text{strength}_e) - \sum_{c \in \text{Contradict}} 0.10 + \Delta_{\text{experiment}}$$

Where $\Delta_{\text{experiment}}$ is:
- $+0.35$ if the hypothesis's experiment achieved `VERIFIED`
- $-0.30$ if the hypothesis's experiment was `REJECTED`
- $0.00$ if `INCONCLUSIVE`

### Normalization

Raw scores are clamped to $[0.01, 0.99]$ to prevent complete zeroing before evidence synthesis is complete, and normalized across all active candidates:

$$S_{\text{final}}(H_i) = \frac{\text{RawScore}(H_i)}{\sum_{j=1}^N \text{RawScore}(H_j)}$$

---

## Agent Pipeline & Model Routing

IncidentForge leverages an OpenAI-compatible Gateway to **Featherless AI** with role-based model routing, combined with structured schema enforcement and deterministic fallbacks.

```mermaid
graph TD
    A[Agent Call Request] --> GW{Featherless Configured?}
    
    GW -- Yes --> ROUTER[Model Router]
    ROUTER -->|DEEP_REASONING| M_DEEP[Kimi-K2 / Deep Reasoning Models]
    ROUTER -->|FAST_REASONING| M_FAST[Llama-3-8B / Qwen-7B Models]
    ROUTER -->|SYNTHESIS| M_SYN[GLM / Synthesis Models]
    
    M_DEEP --> JSON_PARSER[Structured Output Parser]
    M_FAST --> JSON_PARSER
    M_SYN --> JSON_PARSER
    
    JSON_PARSER -->|Valid Schema| DOMAIN[Domain Contracts]
    JSON_PARSER -->|Parse Failure| RETRY[Repair & Retry Loop]
    RETRY --> JSON_PARSER
    
    GW -- No (Demo Mode) --> DET_AGENTS[Deterministic Scenario Agents]
    DET_AGENTS --> DOMAIN
```

### Specialized Agents

1. **`TriageAgent` (`packages/agents/triage.py`)**
   - *Role*: `FAST_REASONING`
   - *Input*: Incident title, description, initial telemetry snapshot, recent events.
   - *Responsibility*: Classifies incident classification, severity (`SEV_1`-`SEV_4`), blast radius, and abnormal symptom identification. Strictly prohibited from claiming root cause.

2. **`EvidenceAnalyst` (`packages/agents/evidence.py`)**
   - *Role*: `FAST_REASONING`
   - *Input*: Triage summary, active symptoms, scenario event logs, historical incident summaries.
   - *Responsibility*: Extracts structured evidence items, rates evidence strength ($0.0 \dots 1.0$), maps initial support/contradiction links, and notes telemetry gaps.

3. **`HypothesisGenerator` (`packages/agents/hypothesis.py`)**
   - *Role*: `DEEP_REASONING`
   - *Input*: Triage output, symptoms, collected evidence items.
   - *Responsibility*: Formulates mutually competing causal hypotheses. Generates explicit, testable quantitative metric predictions for each hypothesis.

4. **`AdversarialCritic` (`packages/agents/critic.py`)**
   - *Role*: `DEEP_REASONING`
   - *Input*: Leading hypothesis, competing hypotheses, evidence corpus.
   - *Responsibility*: Identifies confirmation bias, implicit assumptions, and contradictory evidence. Designs falsification challenges and recommends decisive experimental interventions.

5. **`ExperimentDesigner` (`packages/agents/experiment_designer.py`)**
   - *Role*: `DEEP_REASONING`
   - *Input*: Target hypothesis, critique recommendations, available registered interventions, current telemetry.
   - *Responsibility*: Specifies exact intervention parameters, control variables, expected metric directions/thresholds, and observation window durations.

6. **`RemediationAgent` (`packages/agents/remediation.py`)**
   - *Role*: `SYNTHESIS`
   - *Input*: Verified hypothesis, root-cause evidence, experiment summary, target service.
   - *Responsibility*: Constructs precise code diffs, configuration patches, or rollback plans, along with step-by-step verification instructions.

7. **`DeterministicScenarioAgents` (`packages/agents/deterministic.py`)**
   - *Role*: Fallback / Demo Engine
   - *Responsibility*: Provides zero-dependency, reproducible investigation outputs for local development and offline demonstrations when no API key is present.

---

## Investigation State Machine

The state machine (`packages/orchestration/state_machine.py`) guarantees investigation integrity. Agents cannot skip phases, and invalid transitions raise explicit `IllegalTransition` exceptions.

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> INGESTING
    CREATED --> FAILED
    
    INGESTING --> TRIAGING
    INGESTING --> FAILED
    
    TRIAGING --> EVIDENCE_COLLECTION
    TRIAGING --> FAILED
    
    EVIDENCE_COLLECTION --> HYPOTHESIS_GENERATION
    EVIDENCE_COLLECTION --> FAILED
    
    HYPOTHESIS_GENERATION --> HYPOTHESIS_CRITIQUE
    HYPOTHESIS_GENERATION --> FAILED
    
    HYPOTHESIS_CRITIQUE --> EXPERIMENT_DESIGN
    HYPOTHESIS_CRITIQUE --> FAILED
    
    EXPERIMENT_DESIGN --> EXPERIMENT_VALIDATION
    EXPERIMENT_DESIGN --> FAILED
    
    EXPERIMENT_VALIDATION --> EXPERIMENT_EXECUTION : Approved
    EXPERIMENT_VALIDATION --> EXPERIMENT_DESIGN : Safety Rejected
    EXPERIMENT_VALIDATION --> FAILED
    
    EXPERIMENT_EXECUTION --> OBSERVATION
    EXPERIMENT_EXECUTION --> FAILED
    
    OBSERVATION --> BELIEF_UPDATE
    OBSERVATION --> FAILED
    
    BELIEF_UPDATE --> REMEDIATION : Hypothesis Verified
    BELIEF_UPDATE --> HYPOTHESIS_GENERATION : Hypothesis Rejected
    BELIEF_UPDATE --> EXPERIMENT_DESIGN : Inconclusive Result
    BELIEF_UPDATE --> FAILED
    
    REMEDIATION --> REMEDIATION_VALIDATION
    REMEDIATION --> FAILED
    
    REMEDIATION_VALIDATION --> RESOLVED : Golden Signals Restored
    REMEDIATION_VALIDATION --> REMEDIATION : Validation Failed
    REMEDIATION_VALIDATION --> FAILED
    
    RESOLVED --> [*]
    FAILED --> [*]
```

---

## End-to-End Data Flow

The following sequence diagram outlines how data flows across components during a live investigation:

```mermaid
sequenceDiagram
    autonumber
    actor SRE as SRE / User
    participant Web as Web Command Center
    participant API as FastAPI Backend
    participant Orch as Orchestrator
    participant Agents as AI / Fallback Agents
    participant Twin as Digital Twin
    participant Verif as Verification Engine
    participant Belief as Belief Engine
    participant Mem as Memory Store

    SRE->>Web: Start Investigation
    Web->>API: POST /api/incidents/{id}/start
    API->>Orch: start_investigation(incident_id)
    
    Note over Orch,Agents: Phase 1: Triage & Evidence
    Orch->>Agents: TriageAgent.analyze()
    Agents-->>Orch: TriageOutput (Symptoms, Sev)
    Orch->>API: Publish triage_completed event
    API-->>Web: SSE stream update
    
    Orch->>Agents: EvidenceAnalyst.analyze()
    Agents-->>Orch: Evidence items & correlations
    
    Note over Orch,Agents: Phase 2: Hypotheses & Critique
    Orch->>Agents: HypothesisGenerator.generate()
    Agents-->>Orch: Competing Hypotheses (H1, H2, H3)
    Orch->>Agents: AdversarialCritic.critique(leading_h)
    Agents-->>Orch: Falsification strategy & recommended test
    
    Note over Orch,Twin: Phase 3: Experimentation
    Orch->>Agents: ExperimentDesigner.design()
    Agents-->>Orch: Experiment Spec (Intervention, Thresholds)
    Orch->>Twin: Run Bounded Intervention
    Twin->>Twin: Tick equations over observation window
    Twin-->>Orch: Baseline & Post Telemetry Snapshots
    
    Note over Orch,Belief: Phase 4: Deterministic Verification
    Orch->>Verif: evaluate(experiment, baseline, post)
    Verif-->>Orch: VerificationResult (VERIFIED / REJECTED)
    Orch->>Belief: update(hypotheses, verifications, evidence)
    Belief-->>Orch: Normalized confidence scores
    
    Note over Orch,Mem: Phase 5: Remediation & Resolution
    Orch->>Agents: RemediationAgent.generate(verified_h)
    Agents-->>Orch: Remediation Patch (Diff / Config)
    Orch->>Twin: Apply Remediation & Validate Telemetry
    Twin-->>Orch: Healthy Baselines Restored
    Orch->>Mem: Store incident fingerprint & artifacts
    Orch->>API: Publish incident_resolved event
    API-->>Web: SSE final state & Timeline
```

---

## Infrastructure & Deployment

IncidentForge is containerized for standard cloud and local developer environments.

```mermaid
graph TD
    subgraph Host["Docker Compose Environment"]
        subgraph WebContainer["web (Node.js 20)"]
            NextApp[Next.js 14 Frontend<br/>Port: 3000]
        end
        
        subgraph ApiContainer["api (Python 3.11)"]
            FastAPIApp[FastAPI REST & SSE Service<br/>Port: 8000]
        end
        
        subgraph DBContainer["db (PostgreSQL 17 + pgvector)"]
            PostgresDB[(Incident & Memory Store<br/>Port: 5432)]
        end
        
        subgraph CacheContainer["redis (Redis 7)"]
            RedisCache[(Pub/Sub & Cache<br/>Port: 6379)]
        end
    end

    NextApp -->|HTTP / SSE| FastAPIApp
    FastAPIApp --> PostgresDB
    FastAPIApp --> RedisCache
```

### Components

- **PostgreSQL 17 with `pgvector`**: Persists incidents, timeline events, agent runs, experiments, and incident fingerprints with vector embeddings for cosine similarity lookups.
- **Redis 7**: Provides event streaming pub/sub message queues and distributed caching.
- **FastAPI API Service**: Uvicorn-driven asynchronous Python backend (`apps/api/Dockerfile`).
- **Next.js 14 Web Service**: Standalone Next.js Node container (`apps/web/Dockerfile`) serving the Incident Command Center.

---

## API Layer & Interfaces

The API is fully documented via OpenAPI at `/docs`. Key endpoints include:

### Incident Management

#### `POST /api/incidents`
Creates a new incident record.
```json
// Request
{
  "title": "Checkout latency degradation and error spike",
  "description": "Tail latency exceeded 500ms on /checkout endpoint with cascading 503s.",
  "severity": "SEV_2",
  "service": "checkout-service",
  "scenario_id": "incident-001"
}
```

#### `POST /api/incidents/demo`
Creates an incident pre-loaded from an evaluation scenario and immediately initiates the background investigation workflow.

#### `POST /api/incidents/{id}/start`
Triggers the background execution of the investigation lifecycle orchestrator.

#### `GET /api/incidents/{id}`
Returns full incident details, current state machine status, active symptoms, competing hypotheses with live confidence scores, executed experiments, and remediation status.

#### `GET /api/incidents/{id}/timeline`
Returns an ordered event log of all lifecycle milestones, agent executions, verification decisions, and state transitions.

#### `GET /api/incidents/{id}/events`
Server-Sent Events (SSE) stream delivering real-time lifecycle event updates directly to the frontend.

---

### Experiments & Remediation

#### `GET /api/experiments/{experiment_id}`
Fetches experiment configuration, target hypothesis, intervention parameters, expected condition thresholds, observation snapshots, and verification audit trails.

#### `GET /api/incidents/{incident_id}/remediation`
Fetches the generated remediation proposal, including unified diffs, configuration patches, and post-fix validation status.

---

### System, Memory & Counterfactuals

#### `GET /api/incidents/{incident_id}/memory`
Retrieves institutional memory records stored for a resolved incident.

#### `GET /api/memory/similar/{incident_id}`
Returns historical incident records with high semantic and symptom similarity.

#### `GET /api/incidents/{incident_id}/counterfactual`
Executes a counterfactual replay on the Digital Twin comparing the actual incident impact against an earlier intervention point, computing estimated avoided user failures.

#### `GET /api/health`
Returns system operational status, active reasoning mode (`live_model` vs `deterministic_demo`), and Featherless gateway connectivity.

```json
// Response
{
  "status": "ok",
  "reasoning_mode": "live_model",
  "featherless_configured": true,
  "simulation_only": true
}
```

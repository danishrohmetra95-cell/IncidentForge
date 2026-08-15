# IncidentForge

> **AI-powered incident response through experimental reasoning and deterministic verification**

*"AI proposes. Evidence challenges. Experiments test. Deterministic software verifies."*

---

## The Problem

Incident response today relies heavily on correlation, tribal knowledge, and gut instinct. When outages occur, on-call engineers often jump to conclusions based on surface-level dashboard anomalies and past trauma without rigorously testing their hypotheses. This leads to:

- **Misdirected remediation**: Applying fixes to symptoms rather than root causes, worsening outages.
- **Extended Mean Time to Resolution (MTTR)**: Wasting critical minutes or hours pursuing false leads.
- **Confirmation bias**: Forcing telemetry to fit pre-conceived notions instead of following empirical proof.

## The Solution

IncidentForge treats every incident as a **scientific investigation**. 

Rather than relying on simple pattern matching or static playbooks, IncidentForge:
1. Generates competing root-cause hypotheses based on observed telemetry and topology.
2. Actively tries to **falsify** each hypothesis through counter-evidence and automated critiques.
3. Designs and executes safe intervention experiments within a **deterministic Digital Twin**.
4. Declares a verified root cause **only** when deterministic verification software confirms the hypothesis under controlled experimental conditions.

---

## How It Works

### Investigation Lifecycle

```
INCIDENT ──▶ TRIAGE ──▶ EVIDENCE ──▶ HYPOTHESES ──▶ CRITIQUE ──▶ EXPERIMENT ──▶ VERIFY ──▶ REMEDIATE
```

### The Key Differentiator: *Correlation is Not Proof*

Most observability and AIOps tools stop at correlation: *"Metric A spiked right when Metric B dropped, so A caused B."* 

IncidentForge closes the causal loop:
1. **AI Proposes & Designs Interventions**: Generates candidate hypotheses and specific, falsifiable experimental tests.
2. **Digital Twin Executes**: Safely runs the intervention against a deterministic model of the service architecture.
3. **Metrics Change**: Measures dynamic system response and counterfactual behavior.
4. **Deterministic Verifier**: Evaluates hard invariant bounds and causal contracts — *"Hypothesis verified."*

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, Pydantic |
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts, React Flow |
| **AI / Reasoning** | Featherless AI (OpenAI-compatible) with deterministic fallback agents |
| **Database & Memory** | PostgreSQL with `pgvector` for incident embeddings and long-term memory |
| **Cache & Queues** | Redis |
| **Infrastructure** | Docker, Docker Compose |

---

## Quick Start

### Prerequisites
- [Python 3.11+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)
- [Docker & Docker Compose](https://www.docker.com/)

---

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/danishrohmetra95-cell/IncidentForge.git
cd IncidentForge

# Copy environment template
cp .env.example .env

# Start all services
docker compose up --build
```

---

### Manual Setup

```bash
# 1. Start database and Redis
make dev-db

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run database migrations
make migrate

# 4. Start the API server
make api

# 5. In a separate terminal, start the frontend
cd apps/web && npm install && npm run dev
```

- **API Server & OpenAPI Docs**: [http://localhost:8000](http://localhost:8000) / [http://localhost:8000/docs](http://localhost:8000/docs)
- **Incident Command Center (Frontend)**: [http://localhost:3000](http://localhost:3000)

---

## Demo Mode

IncidentForge supports two execution modes:

- **Live Model Mode**: Leverages Featherless AI for LLM-driven hypothesis generation, adversarial critique, and remediation planning (requires `FEATHERLESS_API_KEY` in `.env`).
- **Deterministic Demo Mode**: Uses built-in deterministic agents producing reproducible, verifiable results out-of-the-box without requiring an external API key.

To trigger an automated demo run:

```bash
curl -X POST http://localhost:8000/api/incidents/demo
```

---

## Project Structure

```
IncidentForge/
├── apps/
│   ├── api/          # FastAPI backend service
│   └── web/          # Next.js frontend (Incident Command Center)
├── packages/
│   ├── agents/       # AI agents (triage, hypothesis, critic, experiment, remediation)
│   ├── contracts/    # Domain models, agent I/O contracts, events
│   ├── experiments/  # Experiment engine, counterfactual analysis
│   ├── llm/          # Featherless AI gateway, model routing
│   ├── memory/       # Incident memory, fingerprinting, embeddings
│   ├── orchestration/# Investigation orchestrator, state machine
│   ├── reasoning/    # Verification engine, belief update, safety
│   └── simulator/    # Deterministic Digital Twin
├── scenarios/        # Incident scenario fixtures & telemetry
├── tests/            # Unit, integration, contract, and E2E tests
├── database/         # Database initialization and migrations
├── docs/             # Architecture documentation
└── docker-compose.yml
```

---

## Testing

Run tests across the entire suite:

```bash
# Run all tests
python -m pytest tests/ -v

# Run unit tests only
python -m pytest tests/unit/ -v

# Run end-to-end tests
python -m pytest tests/end_to_end/ -v
```

---

## Scenarios

IncidentForge ships with three built-in incident scenarios designed with deliberate telemetry ambiguity, forcing the system to rely on experimental reasoning rather than surface heuristics:

1. **DB Connection Pool Exhaustion**: Connection leak introduced in a v1.8 deployment leading to cascading latency spikes and timeout cascades.
2. **Cache Stampede**: Mass cache key invalidation creating a thundering herd on backend databases.
3. **Query Regression**: Unoptimized full-table scan query introduced in a v2.1 deployment causing resource starvation.

---

## Architecture

For a deep dive into the system design, agent communication topology, and verification engine, refer to the [Architecture Documentation](docs/architecture.md).

---

## Environment Variables

See [.env.example](.env.example) for a complete list of configuration options, keys, and connection strings.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

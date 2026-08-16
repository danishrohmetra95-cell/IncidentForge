# Digital Twin Simulation Engine

The Digital Twin (`packages/simulator/twin.py`) is the deterministic heart of IncidentForge's falsification engine. Instead of testing potentially destructive patches in production, the AI agents interact exclusively with a sandboxed mathematical simulation of a high-throughput microservices architecture.

## Deterministic Simulation Model

The Digital Twin simulates a continuous, tick-based environment of a `checkout-service` stack:
- **API Gateway**
- **Checkout Application Nodes**
- **PostgreSQL Database**
- **Redis Cache**
- **Async Worker Queues**

The simulation uses coupled causal equations. For example, database utilization depends on effective database queries, which depend on request rate and cache hit rate. If active connections exceed the database pool size, it generates an exponential wait queue, leading to cascading HTTP timeouts (errors) and tail latency spikes.

## Telemetry Signals

The twin exposes 9 core observability metrics via `TelemetrySnapshot`:
1. `request_rate` (req/s)
2. `p50_latency` (ms)
3. `p95_latency` (ms)
4. `p99_latency` (ms)
5. `error_rate` (fraction)
6. `db_connections` (count)
7. `db_utilization` (fraction)
8. `cache_hit_rate` (fraction)
9. `cpu` (fraction)

## Supported Fault Scenarios

The simulator natively reproduces three distinct failure modes, each with unique cascading symptoms:

1. **`incident-001-db-pool` (Connection Leak)**
   - Connections leak during checkout, saturating the DB pool.
   - Symptoms: `p95_latency` spikes, `db_connections` hits maximum.
2. **`incident-002-cache-stampede` (Cache Stampede)**
   - Redis cache invalidation causes direct database hits.
   - Symptoms: `cache_hit_rate` drops to <20%, `db_utilization` hits 99%, `cpu` spikes.
3. **`incident-003-query-regression` (Unindexed Query)**
   - A new deployment introduces a missing DB index, increasing query cost from 15ms to 60ms.
   - Symptoms: `cpu` spikes, `queue_depth` grows, but `db_connections` remains stable.

## Registered Interventions

AI agents can only execute sandboxed actions registered in the `InterventionRegistry`. The twin translates these actions into deterministic parameter shifts:

- `connection_pool_reset`: Restores connections to 10% capacity.
- `cache_flush`: Drops cache hit rate drastically to test recovery.
- `cache_ttl_change`: Modifies TTL duration.
- `deployment_rollback`: Reverts application version (e.g., v1.8 back to v1.7).
- `feature_flag_disable`: Toggles specific application features.
- `worker_restart`: Flushes the async queue.

## Experiment Mechanics

When an experiment is executed:
1. **Baseline**: The orchestrator observes the twin *before* the intervention.
2. **Intervention**: The `ExperimentEngine` applies the AI-proposed intervention.
3. **Tick**: The twin advances forward in time (e.g., 20 ticks) to allow the system to stabilize under the new conditions.
4. **Observation**: The orchestrator observes the twin *after* the intervention.
5. **Boundary**: The resulting snapshots are handed over to the pure-software `VerificationEngine`.

Because the twin is entirely mathematical, it guarantees that correct interventions fix the root cause, and incorrect interventions either do nothing or worsen the situation—falsifying wrong guesses deterministically.

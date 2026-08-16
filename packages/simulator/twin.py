"""Digital Twin — deterministic production-service simulation.

Simulates a checkout service environment with causally meaningful
equations. Metrics are derived from internal state, never from an LLM.

The primary scenario (incident-001) begins with ambiguous telemetry
supporting multiple plausible hypotheses simultaneously.
"""

import copy
import math
from packages.contracts.domain import TelemetrySnapshot


class DigitalTwin:
    """Deterministic simulation of a checkout service stack.

    Components modeled:
      API Gateway → Checkout Service → PostgreSQL, Redis (cache), Worker Queue

    Causal chains:
      connection_pressure → wait_time → latency → timeout_prob → error_rate
      cache_miss_rate → db_load → cpu → latency
      query_cost → cpu → queue_depth → latency
    """

    def __init__(self):
        # Infrastructure parameters
        self.deployment_version = "v1.7"
        self.db_pool_size = 100
        self.active_connections = 20
        self.request_rate = 1500.0
        self.cache_hit_rate = 0.95
        self.db_query_cost_ms = 15.0
        self.cpu_load = 0.25
        self.queue_depth = 0
        self.memory_usage = 0.40
        self.feature_flags: dict[str, bool] = {"new_checkout_flow": False}
        self.base_latency_ms = 45.0

        # Fault state
        self._fault_type: str | None = None
        self._fault_params: dict = {}
        self._cpu_overhead = 0.0

        # Derived metrics (updated on tick)
        self._p50_latency = 50.0
        self._p95_latency = 60.0
        self._p99_latency = 80.0
        self._error_rate = 0.001
        self._db_utilization = 0.20

    # ── Fault injection ──────────────────────────────────────────

    def inject_fault(self, fault_config: dict) -> None:
        """Load a fault scenario into the twin."""
        self._fault_type = fault_config.get("type")
        self._fault_params = dict(fault_config)

        if "deployment_version" in fault_config:
            self.deployment_version = fault_config["deployment_version"]

        # Pre-condition the twin to match the scenario's initial telemetry
        if self._fault_type == "connection_leak":
            # Start with connections already elevated
            self.active_connections = int(self.db_pool_size * 0.85)
            self.request_rate = fault_config.get("request_rate", 1800.0)
            # Mild cache degradation adds ambiguity
            cache_degrade = fault_config.get("initial_cache_degradation", 0.15)
            self.cache_hit_rate = max(0.60, 0.95 - cache_degrade)
            self._cpu_overhead = fault_config.get("cpu_overhead", 0.08)

        elif self._fault_type == "cache_stampede":
            self.request_rate = fault_config.get("request_rate", 1800.0)
            self.cache_hit_rate = fault_config.get("initial_cache_hit_rate", 0.15)
            self.active_connections = int(self.db_pool_size * 0.4)

        elif self._fault_type == "query_regression":
            self.request_rate = fault_config.get("request_rate", 1800.0)
            self.db_query_cost_ms = fault_config.get("query_cost_ms", 60.0)
            self.active_connections = int(self.db_pool_size * 0.35)

        elif self._fault_type == "upstream_latency":
            self.request_rate = fault_config.get("request_rate", 1000.0)
            self.active_connections = int(self.db_pool_size * 0.3)
            self.cache_hit_rate = 0.95
            self._p95_latency = 875.0
            self._error_rate = 0.008

        # Run a few ticks to stabilize derived metrics
        self.tick(steps=5)

    # ── Simulation step ──────────────────────────────────────────

    def tick(self, steps: int = 1) -> None:
        """Advance simulation by N steps. All equations are deterministic."""
        for _ in range(steps):
            # ─ Fault progression ─
            if self._fault_type == "connection_leak":
                leak_rate = self._fault_params.get("leak_rate", 3)
                self.active_connections = min(
                    self.active_connections + leak_rate,
                    int(self.db_pool_size * 1.5),
                )
                # Slow cache degradation adds ambiguity to initial telemetry
                if self.cache_hit_rate > 0.65:
                    self.cache_hit_rate -= 0.005

            elif self._fault_type == "cache_stampede":
                # Cache stays low until fixed
                if self.cache_hit_rate > 0.15:
                    self.cache_hit_rate = max(0.10, self.cache_hit_rate - 0.03)

            elif self._fault_type == "query_regression":
                # Query cost stays elevated until rollback
                pass

            # ─ Connection pressure ─
            db_pressure = self.active_connections / max(1, self.db_pool_size)

            # Wait time increases exponentially above 80% pool utilization.
            # The coefficient deliberately makes a saturated pool visibly
            # user-impacting in the primary scenario, not merely a benign
            # internal metric.
            if db_pressure > 0.8:
                wait_time = 150.0 * math.exp((db_pressure - 0.8) * 8.0)
            else:
                wait_time = 0.0

            # ─ Database load from cache misses ─
            cache_misses = self.request_rate * (1.0 - self.cache_hit_rate)
            effective_db_queries = (self.request_rate * 0.3) + (cache_misses * 0.8)

            # ─ DB utilization ─
            self._db_utilization = min(
                1.0,
                (effective_db_queries * self.db_query_cost_ms) / 25000.0
                + db_pressure * 0.3,
            )

            # A saturated database has scheduler / I/O queueing even when
            # connections are available. This lets cache and query faults
            # independently produce latency through coherent causal paths.
            db_saturation_wait = max(0.0, (self._db_utilization - 0.75) * 1600.0)

            # ─ CPU load ─
            cpu_from_queries = effective_db_queries / 12000.0
            cpu_from_connections = self.active_connections / 500.0
            self.cpu_load = min(
                1.0,
                0.15 + cpu_from_queries + cpu_from_connections + self._cpu_overhead,
            )

            # ─ Latency ─
            query_latency = self.db_query_cost_ms * (1.0 + self._db_utilization * 0.5)
            cpu_latency = 0.0
            if self.cpu_load > 0.7:
                cpu_latency = (self.cpu_load - 0.7) * 500.0

            if self._fault_type == "upstream_latency":
                self._p50_latency = 210.0
                self._p95_latency = 875.0
                self._p99_latency = 1240.0
                self._error_rate = 0.008
                continue

            self._p50_latency = self.base_latency_ms + query_latency * 0.5 + cpu_latency * 0.3
            self._p95_latency = (
                self.base_latency_ms + query_latency + wait_time + db_saturation_wait + cpu_latency
            )
            self._p99_latency = self._p95_latency * 1.4 + wait_time * 0.5

            # ─ Error rate from timeouts ─
            timeout_prob = 0.0
            if self._p95_latency > 250:
                timeout_prob += 0.03
            if self._p95_latency > 500:
                timeout_prob += 0.08
            if self._p95_latency > 800:
                timeout_prob += 0.12
            if self.cpu_load > 0.95:
                timeout_prob += 0.10
            self._error_rate = min(1.0, 0.002 + timeout_prob)

            # ─ Queue depth ─
            if self.cpu_load > 0.80 or self._p95_latency > 400:
                self.queue_depth += max(1, int(self.request_rate * 0.015))
            else:
                self.queue_depth = max(0, self.queue_depth - int(self.request_rate * 0.05))

    # ── Interventions ────────────────────────────────────────────

    def apply_intervention(self, intervention_type: str, params: dict) -> None:
        if intervention_type == "connection_pool_reset":
            self.active_connections = int(self.db_pool_size * 0.1)
            # Fix the leak if it's the root cause
            if self._fault_type == "connection_leak":
                self._fault_params["leak_rate"] = 0
                self._cpu_overhead = 0.0

        elif intervention_type == "cache_flush":
            # Flush empties the cache initially, then it recovers normally
            self.cache_hit_rate = 0.05

        elif intervention_type == "cache_ttl_change":
            # Adjusting TTL helps rebuild cache faster
            if self._fault_type == "cache_stampede":
                self.cache_hit_rate = min(0.90, self.cache_hit_rate + 0.60)
                self._fault_type = None  # stampede resolved

        elif intervention_type == "deployment_rollback":
            self.deployment_version = params.get("target_version", "v1.7")
            if self._fault_type == "query_regression":
                self.db_query_cost_ms = 15.0
                self._fault_type = None

        elif intervention_type == "upstream_latency_mitigation":
            if self._fault_type == "upstream_latency":
                self._base_p50_latency = 120
                self._error_rate_base = 0.001
                self._fault_type = None
            elif self._fault_type == "connection_leak":
                self._fault_params["leak_rate"] = 0
                self._cpu_overhead = 0.0
                self._fault_type = None

        elif intervention_type == "feature_flag_disable":
            flag = params.get("flag")
            if flag and flag in self.feature_flags:
                self.feature_flags[flag] = False

        elif intervention_type == "worker_restart":
            self.queue_depth = 0

    # ── Observation ──────────────────────────────────────────────

    def observe(self) -> TelemetrySnapshot:
        """Return current telemetry derived from internal state."""
        return TelemetrySnapshot(
            request_rate=self.request_rate,
            p50_latency=round(self._p50_latency, 1),
            p95_latency=round(self._p95_latency, 1),
            p99_latency=round(self._p99_latency, 1),
            error_rate=round(self._error_rate, 4),
            db_connections=float(self.active_connections),
            db_utilization=round(self._db_utilization, 3),
            cache_hit_rate=round(self.cache_hit_rate, 3),
            cpu=round(self.cpu_load, 3),
            memory=round(self.memory_usage, 3),
            queue_depth=float(self.queue_depth),
        )

    def reset(self) -> None:
        self.__init__()

    def clone(self) -> "DigitalTwin":
        return copy.deepcopy(self)

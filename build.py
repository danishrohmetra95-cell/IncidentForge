import os

BASE = os.path.dirname(os.path.abspath(__file__))

FILES = {
    r"packages\__init__.py": "",
    r"packages\contracts\__init__.py": "",
    r"packages\contracts\domain.py": '''from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class TelemetrySnapshot:
    deployment_version: str
    request_rate: float
    p95_latency: float
    error_rate: float
    db_utilization: float
    cpu: float
    cache_hit_rate: float
    active_connections: int
    queue_depth: int
    memory_usage: float

@dataclass
class MetricExpectation:
    metric: str
    trend: str
    threshold_percentage: float

@dataclass
class Experiment:
    id: str
    intervention_type: str
    params: Dict[str, Any]
    expectations: List[MetricExpectation]
    target: str = "checkout-service"

@dataclass
class ConditionResult:
    metric: str
    expected_trend: str
    actual_change_pct: float
    passed: bool

@dataclass
class VerificationResult:
    status: str
    conditions: List[ConditionResult]

@dataclass
class Observation:
    baseline: TelemetrySnapshot
    post_intervention: TelemetrySnapshot

@dataclass
class CounterfactualResult:
    baseline_failures: int
    intervention_failures: int
    failure_reduction_pct: float
''',
    r"packages\simulator\__init__.py": "",
    r"packages\simulator\twin.py": '''import math
import copy
from packages.contracts.domain import TelemetrySnapshot

class DigitalTwin:
    def __init__(self):
        self.deployment_version = "v1.7"
        self.db_pool_size = 100
        self.active_connections = 20
        self.request_rate = 1500.0
        self.cache_hit_rate = 0.95
        self.db_query_cost_ms = 15.0
        self.cpu_load = 0.35
        self.queue_depth = 0
        self.memory_usage = 0.4
        self.feature_flags = {"new_checkout_flow": False}
        self.base_latency_ms = 45.0
        
        self.fault_type = None
        self.fault_params = {}
        self.cpu_overhead = 0.0
        
        self.p95_latency = 60.0
        self.error_rate = 0.001
        self.db_utilization = 0.2

    def inject_fault(self, fault_config: dict):
        self.fault_type = fault_config.get("type")
        self.fault_params = fault_config
        if "deployment_version" in fault_config:
            self.deployment_version = fault_config["deployment_version"]

    def tick(self, steps: int = 1):
        for _ in range(steps):
            if self.fault_type == "connection_leak":
                leak_rate = self.fault_params.get("leak_rate", 1)
                self.active_connections = min(self.active_connections + leak_rate, self.db_pool_size * 2)
                degrade = self.fault_params.get("initial_cache_degradation", 0.0)
                self.cache_hit_rate = max(0.1, self.cache_hit_rate - (degrade / max(1, steps)))
                self.cpu_overhead = self.fault_params.get("cpu_overhead", 0.0)
            elif self.fault_type == "cache_stampede":
                self.cache_hit_rate = max(0.05, self.cache_hit_rate - 0.8)
            elif self.fault_type == "query_regression":
                self.db_query_cost_ms += 45.0

            db_pressure = self.active_connections / max(1, self.db_pool_size)
            wait_time = (math.exp((db_pressure - 0.8) * 5)) if db_pressure > 0.8 else 0.0

            cache_misses = self.request_rate * (1.0 - self.cache_hit_rate)
            total_db_load = self.request_rate + (cache_misses * 0.8)

            self.db_utilization = min(1.0, (total_db_load * self.db_query_cost_ms) / 20000.0 * max(1, db_pressure))
            self.cpu_load = min(1.0, 0.2 + (total_db_load / 15000.0) + (self.active_connections / 800.0) + self.cpu_overhead)
            self.p95_latency = self.base_latency_ms + self.db_query_cost_ms + wait_time + (self.cpu_load * 150)

            timeout_prob = 0.0
            if self.p95_latency > 300: timeout_prob += 0.05
            if self.p95_latency > 800: timeout_prob += 0.15
            self.error_rate = min(1.0, 0.001 + timeout_prob + (0.1 if self.cpu_load > 0.95 else 0.0))

            if self.cpu_load > 0.85 or self.p95_latency > 500:
                self.queue_depth += int(self.request_rate * 0.02)
            else:
                self.queue_depth = max(0, self.queue_depth - int(self.request_rate * 0.05))

    def apply_intervention(self, intervention_type: str, params: dict):
        if intervention_type == "connection_pool_reset":
            self.active_connections = int(self.db_pool_size * 0.1)
            if self.fault_type == "connection_leak":
                self.fault_params["leak_rate"] = max(0, self.fault_params.get("leak_rate", 1) - 1)
        elif intervention_type == "cache_flush":
            self.cache_hit_rate = 0.05
        elif intervention_type == "cache_ttl_change":
            self.cache_hit_rate = min(0.99, self.cache_hit_rate + 0.1)
        elif intervention_type == "deployment_rollback":
            self.deployment_version = params.get("target_version", "v1.7")
            if self.fault_type in ["query_regression", "connection_leak"]:
                self.fault_type = None
                self.db_query_cost_ms = 15.0
                self.cpu_overhead = 0.0
        elif intervention_type == "feature_flag_disable":
            flag = params.get("flag")
            if flag in self.feature_flags:
                self.feature_flags[flag] = False
        elif intervention_type == "worker_restart":
            self.queue_depth = 0
            self.p95_latency += 200

    def observe(self) -> TelemetrySnapshot:
        return TelemetrySnapshot(
            deployment_version=self.deployment_version,
            request_rate=self.request_rate,
            p95_latency=self.p95_latency,
            error_rate=self.error_rate,
            db_utilization=self.db_utilization,
            cpu=self.cpu_load,
            cache_hit_rate=self.cache_hit_rate,
            active_connections=self.active_connections,
            queue_depth=self.queue_depth,
            memory_usage=self.memory_usage
        )

    def reset(self):
        self.__init__()

    def clone(self) -> 'DigitalTwin':
        return copy.deepcopy(self)
''',
    r"packages\simulator\scenarios.py": '''import json
import os
from packages.simulator.twin import DigitalTwin

class ScenarioLoader:
    def __init__(self, scenarios_dir: str):
        self.scenarios_dir = scenarios_dir

    def load_scenario(self, scenario_id: str) -> tuple[DigitalTwin, dict]:
        scenario_path = os.path.join(self.scenarios_dir, scenario_id, "scenario.json")
        with open(scenario_path, "r") as f:
            data = json.load(f)
        
        twin = DigitalTwin()
        twin.inject_fault(data.get("fault", {}))
        twin.tick(20)
        
        return twin, data
''',
    r"packages\simulator\interventions.py": '''from packages.simulator.twin import DigitalTwin
from packages.contracts.domain import TelemetrySnapshot

class InterventionRegistry:
    def __init__(self):
        self.registered = [
            "connection_pool_reset",
            "cache_flush",
            "cache_ttl_change",
            "deployment_rollback",
            "feature_flag_disable",
            "worker_restart"
        ]

    def is_registered(self, intervention_type: str) -> bool:
        return intervention_type in self.registered

    def validate(self, twin: DigitalTwin, params: dict) -> bool:
        return True

    def execute(self, twin: DigitalTwin, intervention_type: str, params: dict):
        if not self.is_registered(intervention_type):
            raise ValueError(f"Intervention {intervention_type} not registered.")
        twin.apply_intervention(intervention_type, params)

    def observe(self, twin: DigitalTwin) -> TelemetrySnapshot:
        return twin.observe()

    def rollback(self, twin: DigitalTwin, intervention_type: str, params: dict):
        pass
''',
    r"packages\reasoning\__init__.py": "",
    r"packages\reasoning\verification.py": '''from packages.contracts.domain import Experiment, TelemetrySnapshot, VerificationResult, ConditionResult

class VerificationEngine:
    def evaluate(self, experiment: Experiment, baseline: TelemetrySnapshot, post: TelemetrySnapshot) -> VerificationResult:
        conditions = []
        passes = 0
        
        for exp in experiment.expectations:
            base_val = getattr(baseline, exp.metric)
            post_val = getattr(post, exp.metric)
            
            if base_val == 0:
                pct_change = 0.0
            else:
                pct_change = ((post_val - base_val) / base_val) * 100.0
                
            passed = False
            if exp.trend == "decrease":
                passed = pct_change <= -exp.threshold_percentage
            elif exp.trend == "increase":
                passed = pct_change >= exp.threshold_percentage
            elif exp.trend == "stable":
                passed = abs(pct_change) < 5.0
                
            conditions.append(ConditionResult(
                metric=exp.metric,
                expected_trend=exp.trend,
                actual_change_pct=pct_change,
                passed=passed
            ))
            if passed: passes += 1
            
        total = len(experiment.expectations)
        if total == 0:
            status = "INCONCLUSIVE"
        elif passes == total:
            status = "VERIFIED"
        elif passes < total / 2:
            status = "REJECTED"
        else:
            status = "INCONCLUSIVE"
            
        return VerificationResult(status=status, conditions=conditions)
''',
    r"packages\reasoning\belief.py": '''from typing import Dict, List
from packages.contracts.domain import VerificationResult

class BeliefUpdateEngine:
    def update_beliefs(self, 
                       hypotheses: List[str], 
                       verification_results: Dict[str, VerificationResult], 
                       evidence_counts: Dict[str, int],
                       historical_similarities: Dict[str, bool]) -> Dict[str, float]:
        
        scores = {h: 1.0 for h in hypotheses}
        
        for h in hypotheses:
            scores[h] += evidence_counts.get(h, 0) * 0.1
            vr = verification_results.get(h)
            if vr:
                if vr.status == "VERIFIED":
                    scores[h] += 0.3
                elif vr.status == "REJECTED":
                    scores[h] -= 0.3
            if historical_similarities.get(h):
                scores[h] += 0.05
                
        total = sum(max(0.01, s) for s in scores.values())
        return {h: max(0.01, s) / total for h, s in scores.items()}
''',
    r"packages\reasoning\safety.py": '''from packages.contracts.domain import Experiment
from packages.simulator.interventions import InterventionRegistry
from packages.simulator.twin import DigitalTwin

class SafetyValidator:
    def __init__(self, registry: InterventionRegistry):
        self.registry = registry

    def validate(self, experiment: Experiment, twin: DigitalTwin) -> tuple[bool, list]:
        reasons = []
        if not experiment.intervention_type:
            reasons.append("Missing intervention_type")
            
        if not self.registry.is_registered(experiment.intervention_type):
            reasons.append(f"Intervention {experiment.intervention_type} is not registered.")
            
        if experiment.target != "checkout-service":
            reasons.append("Target service not found in twin.")
                
        return len(reasons) == 0, reasons
''',
    r"packages\experiments\__init__.py": "",
    r"packages\experiments\engine.py": '''from packages.contracts.domain import Experiment, Observation, VerificationResult
from packages.simulator.twin import DigitalTwin
from packages.simulator.interventions import InterventionRegistry
from packages.reasoning.safety import SafetyValidator
from packages.reasoning.verification import VerificationEngine

class ExperimentEngine:
    def __init__(self, twin: DigitalTwin, registry: InterventionRegistry):
        self.twin = twin
        self.registry = registry
        self.safety_validator = SafetyValidator(registry)
        self.verification_engine = VerificationEngine()

    def run_experiment(self, experiment: Experiment, observation_window: int = 5) -> tuple[Observation, VerificationResult]:
        approved, reasons = self.safety_validator.validate(experiment, self.twin)
        if not approved:
            raise ValueError(f"Safety validation failed: {reasons}")
            
        baseline = self.twin.observe()
        
        self.registry.execute(self.twin, experiment.intervention_type, experiment.params)
        self.twin.tick(observation_window)
        
        post_intervention = self.twin.observe()
        
        observation = Observation(baseline=baseline, post_intervention=post_intervention)
        verification = self.verification_engine.evaluate(experiment, baseline, post_intervention)
        
        return observation, verification
''',
    r"packages\experiments\counterfactual.py": '''from packages.simulator.twin import DigitalTwin
from packages.contracts.domain import CounterfactualResult

class CounterfactualEngine:
    def evaluate(self, twin_at_incident_start: DigitalTwin, intervention_type: str, params: dict, ticks: int = 10) -> CounterfactualResult:
        baseline_twin = twin_at_incident_start.clone()
        baseline_twin.tick(ticks)
        baseline_failures = int(baseline_twin.error_rate * baseline_twin.request_rate * ticks)
        
        intervention_twin = twin_at_incident_start.clone()
        intervention_twin.apply_intervention(intervention_type, params)
        intervention_twin.tick(ticks)
        intervention_failures = int(intervention_twin.error_rate * intervention_twin.request_rate * ticks)
        
        reduction = 0.0
        if baseline_failures > 0:
            reduction = ((baseline_failures - intervention_failures) / baseline_failures) * 100.0
            
        return CounterfactualResult(
            baseline_failures=baseline_failures,
            intervention_failures=intervention_failures,
            failure_reduction_pct=reduction
        )
''',
    r"scenarios\incident-001-db-pool\scenario.json": '''{
  "id": "incident-001-db-pool",
  "title": "Checkout API Degradation",
  "description": "P95 latency spiking, error rate climbing, multiple services showing stress",
  "service": "checkout-service",
  "severity": "SEV_1",
  "fault": {
    "type": "connection_leak",
    "deployment_version": "v1.8",
    "leak_rate": 3,
    "initial_cache_degradation": 0.15,
    "cpu_overhead": 0.08
  },
  "initial_telemetry": {
    "request_rate": 1800,
    "p95_latency": 842,
    "error_rate": 0.214,
    "db_utilization": 0.96,
    "cpu": 0.78,
    "cache_hit_rate": 0.72
  },
  "expected_root_cause": "DB connection pool exhaustion due to connection lifecycle regression in v1.8",
  "ambiguity_note": "Initial telemetry shows elevated CPU and degraded cache hit rate alongside DB pressure, making cache stampede and query regression plausible alternatives"
}''',
    r"scenarios\incident-002-cache-stampede\scenario.json": '''{
  "id": "incident-002-cache-stampede",
  "title": "Redis Cluster Degradation",
  "description": "Cache hit rate plummeted, DB load spiking",
  "service": "checkout-service",
  "severity": "SEV_2",
  "fault": {
    "type": "cache_stampede"
  },
  "initial_telemetry": {
    "request_rate": 1500,
    "p95_latency": 450,
    "error_rate": 0.05,
    "db_utilization": 0.99,
    "cpu": 0.85,
    "cache_hit_rate": 0.15
  },
  "expected_root_cause": "Cache stampede due to mass invalidation",
  "ambiguity_note": "Looks somewhat like a DB query regression"
}''',
    r"scenarios\incident-003-query-regression\scenario.json": '''{
  "id": "incident-003-query-regression",
  "title": "Slow Queries Post Deployment",
  "description": "Database queries taking significantly longer, queues filling up",
  "service": "checkout-service",
  "severity": "SEV_2",
  "fault": {
    "type": "query_regression",
    "deployment_version": "v2.1"
  },
  "initial_telemetry": {
    "request_rate": 1500,
    "p95_latency": 600,
    "error_rate": 0.08,
    "db_utilization": 0.90,
    "cpu": 0.60,
    "cache_hit_rate": 0.95
  },
  "expected_root_cause": "Unoptimized query deployed in v2.1",
  "ambiguity_note": "Could be confused with connection leaks"
}'''
}

for p, c in FILES.items():
    full = os.path.join(BASE, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(c)
print("SUCCESS")

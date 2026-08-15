"""Service factory — wires together agents, engines, and the orchestrator.

This is the composition root. It constructs the full investigation
pipeline from individual components.
"""

import logging
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from packages.llm.gateway import ModelGateway
from packages.llm.routing import ModelRouter
from packages.agents.triage import TriageAgent
from packages.agents.evidence import EvidenceAnalyst
from packages.agents.hypothesis import HypothesisEngine
from packages.agents.critic import AdversarialCritic
from packages.agents.experiment_designer import ExperimentDesigner
from packages.agents.remediation import RemediationAgent
from packages.agents.deterministic import DeterministicScenarioAgents
from packages.experiments.engine import ExperimentEngine
from packages.experiments.counterfactual import CounterfactualEngine
from packages.reasoning.verification import VerificationEngine
from packages.reasoning.belief import BeliefUpdateEngine
from packages.reasoning.safety import SafetyValidator
from packages.simulator.twin import DigitalTwin
from packages.simulator.interventions import InterventionRegistry
from packages.simulator.scenarios import create_twin_from_scenario
from packages.memory.store import IncidentMemoryStore
from packages.memory.fingerprint import IncidentFingerprinter
from packages.orchestration.orchestrator import InvestigationOrchestrator
from apps.api.routes.events import create_event_listener
from apps.api.config import settings

logger = logging.getLogger("incidentforge.services")

# Singleton instances
_gateway: ModelGateway | None = None
_router: ModelRouter | None = None
_memory_store: IncidentMemoryStore | None = None


def get_gateway() -> ModelGateway:
    global _gateway
    if _gateway is None:
        _gateway = ModelGateway(
            api_key=settings.FEATHERLESS_API_KEY,
            base_url=settings.FEATHERLESS_BASE_URL,
            timeout=settings.MODEL_TIMEOUT_SECONDS,
        )
    return _gateway


async def get_router() -> ModelRouter:
    global _router
    if _router is None:
        _router = ModelRouter(get_gateway())
        try:
            await _router.discover_models()
        except Exception as e:
            logger.warning("Model discovery failed: %s", e)
    return _router


def get_memory_store() -> IncidentMemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = IncidentMemoryStore()
    return _memory_store


async def build_orchestrator(incident_id: str):
    """Build a fully wired InvestigationOrchestrator.

    Returns (orchestrator, event_listener) so the caller can attach
    additional listeners if needed.
    """
    gateway = get_gateway()
    if gateway.is_configured:
        router = await get_router()
        triage = TriageAgent(gateway, router)
        evidence = EvidenceAnalyst(gateway, router)
        hypothesis = HypothesisEngine(gateway, router)
        critic = AdversarialCritic(gateway, router)
        designer = ExperimentDesigner(gateway, router)
        remediation = RemediationAgent(gateway, router)
    elif settings.DEMO_MODE:
        deterministic_agents = DeterministicScenarioAgents()
        triage = evidence = hypothesis = critic = designer = remediation = deterministic_agents
    else:
        raise RuntimeError(
            "Live model reasoning requires FEATHERLESS_API_KEY. Set DEMO_MODE=true "
            "only for the explicit deterministic simulation demo."
        )

    # Deterministic engines
    registry = InterventionRegistry()
    experiment_engine = ExperimentEngine(registry)
    verification_engine = VerificationEngine()
    belief_engine = BeliefUpdateEngine()
    safety_validator = SafetyValidator(registry)

    # Memory
    memory_store = get_memory_store()
    fingerprinter = IncidentFingerprinter()

    # Event listener for SSE
    event_listener = await create_event_listener(incident_id)

    # Twin factory — creates a configured twin from scenario data
    def twin_factory(scenario_data: dict) -> DigitalTwin:
        return create_twin_from_scenario(scenario_data)

    orchestrator = InvestigationOrchestrator(
        triage_agent=triage,
        evidence_analyst=evidence,
        hypothesis_engine=hypothesis,
        adversarial_critic=critic,
        experiment_designer=designer,
        remediation_agent=remediation,
        experiment_engine=experiment_engine,
        verification_engine=verification_engine,
        belief_engine=belief_engine,
        safety_validator=safety_validator,
        twin_factory=twin_factory,
        memory_store=memory_store,
        fingerprinter=fingerprinter,
        event_listeners=[event_listener],
    )

    return orchestrator, event_listener

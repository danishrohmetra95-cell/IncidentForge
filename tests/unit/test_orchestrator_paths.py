import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from packages.contracts.domain import *
from packages.contracts.agent_io import *
from packages.orchestration.orchestrator import InvestigationOrchestrator, InvestigationContext, MAX_HYPOTHESIS_CYCLES, MAX_EXPERIMENT_ATTEMPTS
from packages.reasoning.verification import VerificationEngine
from packages.reasoning.belief import BeliefUpdateEngine
from packages.reasoning.safety import SafetyValidator
from packages.experiments.engine import ExperimentEngine
from packages.simulator.interventions import InterventionRegistry
from packages.simulator.scenarios import load_scenario, create_twin_from_scenario
from packages.memory.store import IncidentMemoryStore
from packages.memory.fingerprint import IncidentFingerprinter
from packages.agents.deterministic import DeterministicScenarioAgents

# Mock classes to control the agent outputs

class MockAgents(DeterministicScenarioAgents):
    def __init__(self):
        super().__init__()
        self.hypothesis_call_count = 0
        self.experiment_call_count = 0
        self.force_safety_rejection = False
        
    async def generate_hypotheses(self, input_data: HypothesisGenerationInput) -> HypothesisGenerationOutput:
        self.hypothesis_call_count += 1
        output = await super().generate_hypotheses(input_data)
        
        # If we are testing rejection loops, manipulate the hypotheses
        if self.hypothesis_call_count == 1 and hasattr(self, 'first_cycle_hypothesis_statement'):
            output.hypotheses = [
                HypothesisCandidate(
                    statement=self.first_cycle_hypothesis_statement,
                    initial_score=0.99,
                    supporting_evidence_indices=[],
                    predictions=[],
                    reasoning=""
                )
            ]
        elif self.hypothesis_call_count == 2 and hasattr(self, 'second_cycle_hypothesis_statement'):
            output.hypotheses = [
                HypothesisCandidate(
                    statement=self.second_cycle_hypothesis_statement,
                    initial_score=0.99,
                    supporting_evidence_indices=[],
                    predictions=[],
                    reasoning=""
                )
            ]
        return output

    async def design(self, input_data: ExperimentDesignInput) -> ExperimentDesignOutput:
        self.experiment_call_count += 1
        output = await super().design(input_data)
        
        if self.force_safety_rejection and self.experiment_call_count == 1:
            # Provide an intervention that we know safety rejects (e.g. database_drop if it exists)
            # Or just set a parameter that is unsafe. 
            output.intervention = InterventionSpec(type="deployment_rollback", target="prod-db", parameters={"force": True})
        
        # If we want inconclusive, we set up expectations where one condition
        # passes and one fails, yielding INCONCLUSIVE (not majority fail).
        # connection_pool_reset DOES reduce db_connections in the db-pool scenario
        # (PASS), but cache_hit_rate won't increase by 200% (FAIL).
        if hasattr(self, 'first_experiment_inconclusive') and self.first_experiment_inconclusive and self.experiment_call_count == 1:
            output.intervention = InterventionSpec(type="connection_pool_reset", target="postgresql", parameters={})
            output.expected_conditions = [
                MetricExpectation(metric="db_connections", direction=MetricDirection.DECREASE, threshold_percentage=60),
                MetricExpectation(metric="cache_hit_rate", direction=MetricDirection.INCREASE, threshold_percentage=200),
            ]
            
        return output

class TestOrchestratorPaths:
    @pytest.fixture
    def setup_orchestrator(self):
        scenario = load_scenario('incident-001-db-pool')
        incident = Incident(
            title=scenario["title"],
            description=scenario["description"],
            severity=Severity(scenario["severity"]),
            service=scenario["service"],
        )
        
        registry = InterventionRegistry()
        mock_agents = MockAgents()
        
        orchestrator = InvestigationOrchestrator(
            triage_agent=mock_agents,
            evidence_analyst=mock_agents,
            hypothesis_engine=mock_agents,
            adversarial_critic=mock_agents,
            experiment_designer=mock_agents,
            remediation_agent=mock_agents,
            experiment_engine=ExperimentEngine(registry),
            verification_engine=VerificationEngine(),
            belief_engine=BeliefUpdateEngine(),
            safety_validator=SafetyValidator(registry),
            twin_factory=lambda s: create_twin_from_scenario(s),
            memory_store=IncidentMemoryStore(),
            fingerprinter=IncidentFingerprinter(),
        )
        return orchestrator, incident, scenario, mock_agents

    @pytest.mark.asyncio
    async def test_rejected_experiment_triggers_rehypothesis(self, setup_orchestrator):
        orchestrator, incident, scenario, mock_agents = setup_orchestrator
        
        # 1st cycle: Propose "A cache stampede..." which will cause the deterministic agent to 
        # use cache_ttl_change and expect cache_hit_rate to increase by 200%. 
        # But for incident-001-db-pool, cache_ttl_change doesn't help much, and expectations will fail.
        mock_agents.first_cycle_hypothesis_statement = "A cache stampede is driving excess database work."
        
        # 2nd cycle: Propose correct one.
        mock_agents.second_cycle_hypothesis_statement = "Database connection pool exhaustion is delaying checkout requests."
        
        ctx = await orchestrator.run(incident, scenario)
        
        assert ctx.incident.status == InvestigationState.RESOLVED
        assert ctx.hypothesis_cycles == 2
        
        # Check transitions
        history = [s for s in ctx.state_machine.history]
        
        # Find BELIEF_UPDATE -> HYPOTHESIS_GENERATION
        transitions = [(history[i], history[i+1]) for i in range(len(history)-1)]
        assert (InvestigationState.BELIEF_UPDATE, InvestigationState.HYPOTHESIS_GENERATION) in transitions

    @pytest.mark.asyncio
    async def test_inconclusive_experiment_retries_with_new_experiment(self, setup_orchestrator):
        orchestrator, incident, scenario, mock_agents = setup_orchestrator
        
        # We need an inconclusive result.
        mock_agents.first_cycle_hypothesis_statement = "Database connection pool exhaustion is delaying checkout requests."
        mock_agents.first_experiment_inconclusive = True
        
        ctx = await orchestrator.run(incident, scenario)
        
        assert ctx.incident.status == InvestigationState.RESOLVED
        # Cycle 1 only
        assert ctx.hypothesis_cycles == 1
        # Experiment count should be > 1
        assert len(ctx.experiments) >= 2
        
        history = [s for s in ctx.state_machine.history]
        transitions = [(history[i], history[i+1]) for i in range(len(history)-1)]
        assert (InvestigationState.BELIEF_UPDATE, InvestigationState.EXPERIMENT_DESIGN) in transitions

    @pytest.mark.asyncio
    async def test_no_infinite_loops_on_repeated_rejection(self, setup_orchestrator):
        orchestrator, incident, scenario, mock_agents = setup_orchestrator
        
        # Always propose bad hypothesis
        mock_agents.first_cycle_hypothesis_statement = "A cache stampede is driving excess database work."
        mock_agents.second_cycle_hypothesis_statement = "A cache stampede is driving excess database work."
        
        # Force a third cycle to also be bad
        # We can just override generate_hypotheses to always return bad
        async def bad_hypotheses(input_data):
            mock_agents.hypothesis_call_count += 1
            return HypothesisGenerationOutput(
                hypotheses=[
                    HypothesisCandidate(
                        statement="A cache stampede is driving excess database work.",
                        initial_score=0.99,
                        supporting_evidence_indices=[],
                        predictions=[],
                        reasoning=""
                    )
                ],
                rationale=""
            )
        mock_agents.generate_hypotheses = bad_hypotheses
        
        ctx = await orchestrator.run(incident, scenario)
        
        assert ctx.incident.status == InvestigationState.FAILED
        assert ctx.hypothesis_cycles == MAX_HYPOTHESIS_CYCLES
        
    @pytest.mark.asyncio
    async def test_safety_rejected_experiment_redesigns(self, setup_orchestrator):
        orchestrator, incident, scenario, mock_agents = setup_orchestrator
        
        mock_agents.first_cycle_hypothesis_statement = "Database connection pool exhaustion is delaying checkout requests."
        mock_agents.force_safety_rejection = True
        
        ctx = await orchestrator.run(incident, scenario)
        
        assert ctx.incident.status == InvestigationState.RESOLVED
        # One hypothesis cycle
        assert ctx.hypothesis_cycles == 1
        
        history = [s for s in ctx.state_machine.history]
        transitions = [(history[i], history[i+1]) for i in range(len(history)-1)]
        # EXPERIMENT_VALIDATION -> EXPERIMENT_DESIGN on safety rejection
        assert (InvestigationState.EXPERIMENT_VALIDATION, InvestigationState.EXPERIMENT_DESIGN) in transitions

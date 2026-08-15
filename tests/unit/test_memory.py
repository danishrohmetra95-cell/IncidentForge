import pytest
from packages.contracts.domain import Incident, Symptom, Evidence, Severity, EvidenceType, MetricDirection, IncidentMemoryRecord, IncidentFingerprint
from packages.memory.fingerprint import IncidentFingerprinter
from packages.memory.store import IncidentMemoryStore
from apps.api.persistence.repository import IncidentRepository

@pytest.fixture
def sample_symptom():
    return Symptom(
        name="High CPU",
        metric="cpu_usage",
        direction=MetricDirection.INCREASE,
        observed_value=95.0,
        normal_range="40-60"
    )

@pytest.fixture
def sample_symptom2():
    return Symptom(
        name="High Latency",
        metric="p99_latency",
        direction=MetricDirection.INCREASE,
        observed_value=1.5,
        normal_range="0.1-0.2"
    )

def test_fingerprint_never_empty_for_valid_incident(sample_symptom):
    incident = Incident(
        title="Test Incident",
        description="CPU Spike",
        severity=Severity.SEV_2,
        service="api-gateway",
        symptoms=[sample_symptom]
    )
    evidence = [Evidence(
        incident_id=incident.id,
        type=EvidenceType.METRIC,
        source="api-gateway",
        observation="High CPU observed"
    )]
    
    fingerprinter = IncidentFingerprinter()
    fp = fingerprinter.fingerprint(incident, [sample_symptom], evidence)
    
    assert len(fp.services) > 0
    assert "api-gateway" in fp.services
    assert len(fp.symptoms) > 0
    assert fp.symptoms[0] == sample_symptom.description

def test_symptoms_contribute_to_similarity(sample_symptom, sample_symptom2):
    fp1 = IncidentFingerprint(
        services=["api-gateway"],
        metric_patterns=["cpu_usage", "p99_latency"],
        symptoms=[sample_symptom.description, sample_symptom2.description]
    )
    
    fp2 = IncidentFingerprint(
        services=["api-gateway"],
        metric_patterns=["cpu_usage", "p99_latency"],
        symptoms=[sample_symptom.description]
    )
    
    fp3 = IncidentFingerprint(
        services=["api-gateway"],
        metric_patterns=["cpu_usage", "p99_latency"],
        symptoms=[]
    )
    
    fingerprinter = IncidentFingerprinter()
    
    sim_1_2 = fingerprinter.similarity(fp1, fp2)
    sim_1_3 = fingerprinter.similarity(fp1, fp3)
    
    # 1 and 2 share one symptom, 1 and 3 share no symptoms
    assert sim_1_2 > sim_1_3

@pytest.mark.asyncio
async def test_structural_similarity_fallback():
    repo = IncidentRepository()
    
    fp1 = IncidentFingerprint(services=["user-service"], metric_patterns=["error_rate"], symptoms=["high errors"])
    fp2 = IncidentFingerprint(services=["user-service"], metric_patterns=["error_rate"], symptoms=["different errors"])
    
    mem1 = IncidentMemoryRecord(
        incident_id="inc1",
        fingerprint=fp1,
        root_cause="Bad config",
        experiment_summary="Exp 1",
        verified_intervention="Rolled back",
        remediation_summary="Done"
    )
    mem2 = IncidentMemoryRecord(
        incident_id="inc2",
        fingerprint=fp2,
        root_cause="DB down",
        experiment_summary="Exp 2",
        verified_intervention="Scaled up",
        remediation_summary="Done"
    )
    
    await repo.save_memory(mem1)
    await repo.save_memory(mem2)
    
    search_fp = IncidentFingerprint(services=["user-service"], metric_patterns=["error_rate"], symptoms=["high errors"])
    
    results = await repo.find_similar_memories(search_fp, limit=1)
    
    assert len(results) == 1
    assert results[0].incident_id == "inc1"

@pytest.mark.asyncio
async def test_repository_find_similar_delegates():
    repo = IncidentRepository()
    
    fp = IncidentFingerprint(services=["auth-service"])
    mem = IncidentMemoryRecord(
        incident_id="inc1",
        fingerprint=fp,
        root_cause="Test",
        experiment_summary="Test",
        verified_intervention="Test",
        remediation_summary="Test"
    )
    
    await repo.save_memory(mem)
    
    search_fp = IncidentFingerprint(services=["auth-service"])
    results = await repo.find_similar_memories(search_fp, limit=10)
    
    assert len(results) > 0
    assert results[0].incident_id == "inc1"


@pytest.mark.asyncio
async def test_repository_uses_its_memory_store_as_the_search_authority():
    """Repository writes and searches through the supplied shared store."""
    store = IncidentMemoryStore()
    repo = IncidentRepository(memory_store=store)
    fingerprint = IncidentFingerprint(services=["catalog-service"])
    memory = IncidentMemoryRecord(
        incident_id="inc_shared",
        fingerprint=fingerprint,
        root_cause="Catalog database saturation",
        experiment_summary="Reset the pool",
        verified_intervention="connection_pool_reset",
        remediation_summary="Corrected pool sizing",
    )

    await repo.save_memory(memory)

    direct = await store.find_similar(fingerprint)
    via_repository = await repo.find_similar_memories(fingerprint, limit=5)
    assert [item.id for item in via_repository] == [item.id for item in direct]

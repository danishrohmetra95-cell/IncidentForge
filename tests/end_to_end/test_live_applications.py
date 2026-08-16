import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from apps.api.main import app
from packages.contracts.domain import HealthStatus, LiveApplicationObservation, InvestigationState
from apps.api.routes.incidents import _run_investigation

client = TestClient(app)

@pytest.mark.asyncio
async def test_healthy_live_observation():
    obs = LiveApplicationObservation(
        application_url="https://healthy.com",
        status=HealthStatus.HEALTHY,
        http_status=200,
        availability=1.0,
        error_rate=0.0
    )
    
    async def mock_observe(url): return obs
    
    with patch("packages.observability.connector.ApplicationConnector.observe", side_effect=mock_observe):
        res = client.post("/api/applications/connect", json={"url": "https://healthy.com"})
        
    obs_id = res.json()["observation"]["id"]
    
    res = client.post(f"/api/applications/{obs_id}/create-incident")
    assert res.status_code == 200
    inc_id = res.json()["incident_id"]
    
    res = client.get(f"/api/incidents/{inc_id}")
    inc = res.json()
    assert inc["status"] == InvestigationState.RESOLVED.value
    assert inc["reasoning_mode"] == "live_model"
    
    res = client.post(f"/api/incidents/{inc_id}/start")
    assert res.status_code == 400

@pytest.mark.asyncio
async def test_degraded_live_observation_inconclusive():
    obs = LiveApplicationObservation(
        application_url="https://degraded.com",
        status=HealthStatus.DEGRADED,
        http_status=500,
        availability=0.5,
        error_rate=0.5
    )
    
    async def mock_observe(url): return obs
    
    with patch("packages.observability.connector.ApplicationConnector.observe", side_effect=mock_observe):
        res = client.post("/api/applications/connect", json={"url": "https://degraded.com"})
        
    obs_id = res.json()["observation"]["id"]
    
    res = client.post(f"/api/applications/{obs_id}/create-incident")
    inc_id = res.json()["incident_id"]
    
    res = client.get(f"/api/incidents/{inc_id}")
    inc = res.json()
    assert inc["status"] == InvestigationState.CREATED.value
    
    await _run_investigation(inc_id)
    
    res = client.get(f"/api/incidents/{inc_id}")
    inc = res.json()
    print("STATUS", inc["status"])
    print("HYPOTHESES COUNT", inc.get("hypothesis_count"))
    
    # Let's get the full state if needed
    from apps.api.persistence.repository import get_repository
    repo = get_repository()
    ctx = repo._contexts.get(inc_id)
    if ctx:
        print("HYPOTHESES", [h.statement for h in ctx.hypotheses])
    
    assert inc["status"] == InvestigationState.RESOLVED.value
    assert inc["reasoning_mode"] == "live_model"


import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_api_404_nonexistent_incident() -> None:
    response = client.get("/api/incidents/inc_does_not_exist")
    assert response.status_code == 404

def test_api_404_nonexistent_incident_timeline() -> None:
    response = client.get("/api/incidents/inc_does_not_exist/timeline")
    assert response.status_code == 404

def test_api_404_nonexistent_incident_evidence() -> None:
    response = client.get("/api/incidents/inc_does_not_exist/evidence")
    assert response.status_code == 404

def test_api_404_nonexistent_incident_hypotheses() -> None:
    response = client.get("/api/incidents/inc_does_not_exist/hypotheses")
    assert response.status_code == 404

def test_api_422_malformed_request() -> None:
    # Missing required 'title' and 'description'
    response = client.post("/api/incidents", json={"service": "test"})
    assert response.status_code == 422

def test_api_400_invalid_scenario_id() -> None:
    response = client.post("/api/incidents", json={
        "title": "Test",
        "description": "Test",
        "scenario_id": "invalid_scenario"
    })
    # The route returns 400 for unknown scenario
    assert response.status_code == 400
    assert "Unknown scenario" in response.json()["detail"]

def test_api_404_start_nonexistent_incident() -> None:
    response = client.post("/api/incidents/inc_does_not_exist/start")
    assert response.status_code == 404

def test_api_invalid_experiment_transition() -> None:
    # Create incident
    res = client.post("/api/incidents", json={"title": "T", "description": "D"})
    assert res.status_code == 200
    inc_id = res.json()["id"]

    # Start it twice
    res1 = client.post(f"/api/incidents/{inc_id}/start")
    assert res1.status_code == 200
    
    res2 = client.post(f"/api/incidents/{inc_id}/start")
    # Should be 400 because state is not CREATED
    assert res2.status_code == 400
    assert "already in progress" in res2.json()["detail"]

def test_api_404_nonexistent_hypothesis() -> None:
    response = client.post("/api/hypotheses/hyp_does_not_exist/challenge")
    assert response.status_code == 404

def test_api_404_nonexistent_experiment() -> None:
    response = client.post("/api/experiments/exp_does_not_exist/execute")
    assert response.status_code == 404

def test_api_404_nonexistent_remediation() -> None:
    response = client.post("/api/remediation/rem_does_not_exist/validate")
    assert response.status_code == 404

def test_api_invalid_experiment_transition() -> None:
    pass

def test_api_sse_events() -> None:
    # Instead of blocking the test client, test the endpoint function directly
    import asyncio
    from apps.api.routes.events import stream_events
    
    async def run_test():
        response = await stream_events("inc_123")
        iterator = response.body_iterator
        # Get first element (should be connected event)
        first = await iterator.__anext__()
        assert first["event"] == "connected"
        
    asyncio.run(run_test())




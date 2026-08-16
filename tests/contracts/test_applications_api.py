import pytest
from fastapi.testclient import TestClient

from packages.contracts.domain import HealthStatus
from apps.api.main import app

client = TestClient(app)

def test_api_connect_application():
    from unittest.mock import patch
    from packages.contracts.domain import LiveApplicationObservation
    
    obs = LiveApplicationObservation(
        application_url="https://example.com",
        status=HealthStatus.HEALTHY,
        http_status=200,
        availability=1.0,
        error_rate=0.0
    )
    
    # We must patch the async observe method
    async def mock_observe(url): return obs
    
    with patch("packages.observability.connector.ApplicationConnector.observe", side_effect=mock_observe):
        response = client.post(
            "/api/applications/connect",
            json={"url": "https://example.com"}
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "observation" in data
    assert data["observation"]["status"] == "HEALTHY"
    obs_id = data["observation"]["id"]
    
    # Test incident creation
    response = client.post(f"/api/applications/{obs_id}/create-incident")
    assert response.status_code == 200
    assert "incident_id" in response.json()

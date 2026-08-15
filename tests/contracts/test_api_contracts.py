from fastapi.testclient import TestClient

from apps.api.main import app


def test_demo_api_exposes_real_investigation_artifacts() -> None:
    client = TestClient(app)
    created = client.post("/api/incidents/demo")
    assert created.status_code == 200
    incident_id = created.json()["id"]

    incident = client.get(f"/api/incidents/{incident_id}")
    assert incident.status_code == 200
    body = incident.json()
    assert body["status"] == "RESOLVED"
    assert body["reasoning_mode"] == "deterministic_demo"
    assert len(body["hypotheses"]) >= 3
    assert body["verifications"][-1]["outcome"] == "VERIFIED"
    assert body["remediation"]["validation_status"] == "validated"

    memory = client.get(f"/api/incidents/{incident_id}/memory")
    assert memory.status_code == 200
    assert memory.json()["memory"]["root_cause"]


def test_demo_api_honors_the_selected_scenario() -> None:
    client = TestClient(app)
    response = client.post("/api/incidents/demo?scenario_id=incident-002-cache-stampede")

    assert response.status_code == 200
    incident = client.get(f"/api/incidents/{response.json()['id']}")
    assert incident.status_code == 200
    assert incident.json()["scenario_id"] == "incident-002-cache-stampede"

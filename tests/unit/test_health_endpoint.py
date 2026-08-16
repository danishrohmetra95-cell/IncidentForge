import pytest
from httpx import AsyncClient
from apps.api.main import app

@pytest.mark.asyncio
async def test_api_health_endpoint_reports_reasoning_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("FEATHERLESS_API_KEY", "")
    monkeypatch.setenv("XAI_API_KEY", "")
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["reasoning_mode"] == "deterministic_demo"
    assert data["deterministic_fallback_available"] is True
    assert "active_provider" in data

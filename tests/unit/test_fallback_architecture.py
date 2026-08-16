import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic import BaseModel

from packages.llm.gateway import ModelGateway, ModelGatewayUnavailable
from packages.orchestration.orchestrator import InvestigationOrchestrator, InvestigationContext
from packages.contracts.domain import Incident, Severity

class DummySchema(BaseModel):
    message: str

@pytest.fixture
def empty_env(monkeypatch):
    from apps.api.config import settings
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "FEATHERLESS_API_KEY", "")
    monkeypatch.setattr(settings, "XAI_API_KEY", "")

@pytest.fixture
def gemini_env(monkeypatch):
    from apps.api.config import settings
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(settings, "FEATHERLESS_API_KEY", "")
    monkeypatch.setattr(settings, "XAI_API_KEY", "")

@pytest.fixture
def all_env(monkeypatch):
    from apps.api.config import settings
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "gemini-key")
    monkeypatch.setattr(settings, "FEATHERLESS_API_KEY", "featherless-key")
    monkeypatch.setattr(settings, "XAI_API_KEY", "xai-key")

@pytest.mark.asyncio
async def test_no_api_keys_is_not_configured(empty_env):
    gateway = ModelGateway()
    assert not gateway.is_configured
    with pytest.raises(ModelGatewayUnavailable):
        await gateway.generate([{"role": "user", "content": "hello"}], "model")

@pytest.mark.asyncio
async def test_gemini_selected(gemini_env):
    gateway = ModelGateway()
    assert gateway.is_configured
    assert gateway.active_provider_name == "gemini"

@pytest.mark.asyncio
async def test_all_providers_configured_in_order(all_env):
    gateway = ModelGateway()
    assert gateway.is_configured
    assert gateway.active_provider_name == "gemini"
    names = [p.name for p in gateway.providers if p.client is not None]
    assert names == ["gemini", "featherless", "grok"]

@pytest.mark.asyncio
async def test_provider_fallback_on_auth_failure(all_env):
    gateway = ModelGateway()
    
    # Mock the openai clients
    for p in gateway.providers:
        p.client = AsyncMock()
        p.client.chat.completions.create = AsyncMock()

    # Gemini throws Auth failure (APIError, not timeout)
    gateway.providers[0].client.chat.completions.create.side_effect = Exception("Auth Failure")
    
    # Featherless succeeds
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Success"
    gateway.providers[1].client.chat.completions.create.return_value = mock_response

    response = await gateway.generate([{"role": "user", "content": "hi"}], "model")
    assert response == "Success"
    gateway.providers[0].client.chat.completions.create.assert_called()
    gateway.providers[1].client.chat.completions.create.assert_called()
    gateway.providers[2].client.chat.completions.create.assert_not_called()

@pytest.mark.asyncio
async def test_all_live_providers_fail_raises(all_env):
    gateway = ModelGateway()
    for p in gateway.providers:
        p.client = AsyncMock()
        p.client.chat.completions.create = AsyncMock(side_effect=Exception("Unrecoverable"))

    with pytest.raises(Exception, match="Unrecoverable"):
        await gateway.generate([{"role": "user", "content": "hi"}], "model")

@pytest.mark.asyncio
async def test_orchestrator_deterministic_fallback():
    # Test that Orchestrator uses fallback_func when live coro raises
    orc = InvestigationOrchestrator(
        triage_agent=None, evidence_analyst=None, hypothesis_engine=None,
        adversarial_critic=None, experiment_designer=None, remediation_agent=None,
        experiment_engine=None, verification_engine=None, belief_engine=None,
        safety_validator=None, twin_factory=None
    )
    
    ctx = InvestigationContext(Incident(
        title="test", description="test", severity=Severity.SEV_3, service="test"
    ))
    
    async def failing_live_coro():
        raise Exception("Live Model Timeout")
        
    async def fallback_coro():
        return "Deterministic Success"
        
    result = await orc._run_agent(
        ctx, "test_agent", "test_model", failing_live_coro(),
        fallback_func=lambda: fallback_coro()
    )
    
    assert result == "Deterministic Success"
    assert len(ctx.agent_runs) == 1
    assert ctx.agent_runs[0].status == "fallback"

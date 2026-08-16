import pytest
import httpx
from unittest.mock import patch, MagicMock

from packages.observability.connector import ApplicationConnector, SSRFViolationError, is_safe_ip
from packages.contracts.domain import HealthStatus

def test_is_safe_ip():
    assert not is_safe_ip("127.0.0.1")
    assert not is_safe_ip("10.0.0.1")
    assert not is_safe_ip("192.168.1.1")
    assert not is_safe_ip("172.16.0.1")
    assert not is_safe_ip("0.0.0.0")
    assert not is_safe_ip("::1")
    assert not is_safe_ip("fe80::1")
    
    assert is_safe_ip("8.8.8.8")
    assert is_safe_ip("1.1.1.1")

@pytest.mark.asyncio
async def test_connector_ssrf_rejects_localhost():
    obs = await ApplicationConnector.observe("http://localhost:8000")
    assert obs.status == HealthStatus.UNAVAILABLE
    assert "unsafe IP" in obs.error_message or "resolve" in obs.error_message

@pytest.mark.asyncio
async def test_connector_ssrf_rejects_private_ip():
    obs = await ApplicationConnector.observe("http://192.168.1.1")
    assert obs.status == HealthStatus.UNAVAILABLE
    assert "unsafe IP" in obs.error_message

@pytest.mark.asyncio
async def test_connector_http_200():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.is_redirect = False
        mock_resp.content = b"OK"
        async def mock_aread(): pass
        mock_resp.aread = mock_aread
        mock_get.return_value = mock_resp
        
        with patch("packages.observability.connector.resolve_and_check_safety"):
            obs = await ApplicationConnector.observe("https://example.com")
            
        assert obs.status == HealthStatus.HEALTHY
        assert obs.http_status == 200
        assert obs.availability == 1.0
        assert len(obs.latency_samples) == 5

@pytest.mark.asyncio
async def test_connector_http_500():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.is_redirect = False
        mock_resp.content = b"ERROR"
        async def mock_aread(): pass
        mock_resp.aread = mock_aread
        mock_get.return_value = mock_resp
        
        with patch("packages.observability.connector.resolve_and_check_safety"):
            obs = await ApplicationConnector.observe("https://example.com")
            
        assert obs.status == HealthStatus.DEGRADED or obs.status == HealthStatus.UNAVAILABLE
        assert obs.error_rate == 1.0

@pytest.mark.asyncio
async def test_connector_timeout():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        
        with patch("packages.observability.connector.resolve_and_check_safety"):
            obs = await ApplicationConnector.observe("https://example.com")
            
        assert obs.status == HealthStatus.UNAVAILABLE
        assert obs.availability == 0.0
        assert obs.error_rate == 1.0

@pytest.mark.asyncio
async def test_connector_tls_failure():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = httpx.ConnectError("certificate verify failed")
        
        with patch("packages.observability.connector.resolve_and_check_safety"):
            obs = await ApplicationConnector.observe("https://example.com")
            
        assert obs.status == HealthStatus.UNAVAILABLE
        assert obs.tls_valid is False

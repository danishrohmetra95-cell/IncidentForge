import asyncio
import ipaddress
import socket
import logging
from urllib.parse import urlparse
from datetime import datetime

import httpx

from packages.contracts.domain import LiveApplicationObservation, HealthStatus, now

logger = logging.getLogger(__name__)

MAX_REDIRECTS = 3
PROBE_COUNT = 5
PROBE_TIMEOUT = 5.0
MAX_RESPONSE_SIZE = 1024 * 1024  # 1MB

class SSRFViolationError(Exception):
    pass

def is_safe_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        # Block private, loopback, link-local, multicast, reserved
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False
        # Block 0.0.0.0/8 (technically not all private but usually unsafe)
        if ip.version == 4 and str(ip).startswith("0."):
            return False
        return True
    except ValueError:
        return False

async def resolve_and_check_safety(hostname: str) -> None:
    loop = asyncio.get_running_loop()
    try:
        # Resolve all addresses
        addrinfo = await loop.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in addrinfo:
            ip = sockaddr[0]
            if not is_safe_ip(ip):
                raise SSRFViolationError(f"Hostname {hostname} resolves to unsafe IP: {ip}")
    except socket.gaierror:
        # If it can't be resolved, it will fail in httpx anyway. 
        pass

async def safe_fetch(client: httpx.AsyncClient, url: str) -> httpx.Response:
    current_url = url
    redirects = 0
    redirect_chain = []
    
    while redirects <= MAX_REDIRECTS:
        parsed = urlparse(current_url)
        if parsed.scheme not in ("http", "https"):
            raise SSRFViolationError(f"Unsupported scheme: {parsed.scheme}")
        
        if parsed.hostname:
            await resolve_and_check_safety(parsed.hostname)
        
        # We enforce limits on the connection
        response = await client.get(
            current_url, 
            follow_redirects=False, 
            timeout=PROBE_TIMEOUT
        )
        
        # Manually read to enforce max size
        await response.aread()
        if len(response.content) > MAX_RESPONSE_SIZE:
            raise ValueError("Response too large")
            
        redirect_chain.append(current_url)
        
        if response.is_redirect:
            redirects += 1
            current_url = response.headers.get("Location")
            if not current_url:
                break
            # Handle relative redirects
            if not urlparse(current_url).netloc:
                current_url = f"{parsed.scheme}://{parsed.netloc}{current_url}"
        else:
            # Attach the redirect chain for tracing
            response.ext = getattr(response, "ext", {})
            response.ext["redirect_chain"] = redirect_chain
            return response
            
    raise ValueError("Too many redirects")

class ApplicationConnector:
    @staticmethod
    async def observe(url: str) -> LiveApplicationObservation:
        observation = LiveApplicationObservation(application_url=url)
        
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                raise SSRFViolationError("Only HTTP and HTTPS are supported.")
            if parsed.hostname:
                await resolve_and_check_safety(parsed.hostname)
        except Exception as e:
            observation.status = HealthStatus.UNAVAILABLE
            observation.error_message = str(e)
            return observation

        latencies = []
        statuses = []
        errors = 0
        tls_valid = None
        
        async with httpx.AsyncClient(verify=True) as client:
            for _ in range(PROBE_COUNT):
                try:
                    start = datetime.now()
                    resp = await safe_fetch(client, url)
                    end = datetime.now()
                    
                    latency = (end - start).total_seconds() * 1000
                    latencies.append(latency)
                    statuses.append(resp.status_code)
                    
                    if not observation.redirect_chain and hasattr(resp, "ext") and "redirect_chain" in resp.ext:
                        observation.redirect_chain = resp.ext["redirect_chain"]
                        
                    if resp.status_code >= 500:
                        errors += 1
                        
                    if parsed.scheme == "https":
                        tls_valid = True
                        
                except httpx.ConnectError as e:
                    errors += 1
                    if "certificate verify failed" in str(e).lower() or "ssl" in str(e).lower():
                        tls_valid = False
                except (httpx.TimeoutException, ValueError, SSRFViolationError) as e:
                    errors += 1
                except Exception as e:
                    errors += 1
                    
                await asyncio.sleep(0.5)

        if not latencies and errors == PROBE_COUNT:
            observation.status = HealthStatus.UNAVAILABLE
            observation.error_message = "All connection attempts failed."
            observation.availability = 0.0
            observation.error_rate = 1.0
            if tls_valid is not None:
                observation.tls_valid = tls_valid
            return observation
            
        success_count = len(latencies)
        observation.availability = success_count / PROBE_COUNT
        observation.error_rate = errors / PROBE_COUNT
        observation.latency_samples = latencies
        
        if latencies:
            latencies.sort()
            observation.p50_latency = latencies[int(len(latencies) * 0.5)]
            observation.p95_latency = latencies[int(len(latencies) * 0.95)]
            observation.p99_latency = latencies[int(len(latencies) * 0.99)]
            
        if statuses:
            observation.http_status = max(set(statuses), key=statuses.count)
            
        observation.tls_valid = tls_valid
        
        if observation.availability < 0.5:
            observation.status = HealthStatus.UNAVAILABLE
        elif observation.error_rate > 0.1 or (observation.p95_latency and observation.p95_latency > 2000):
            observation.status = HealthStatus.DEGRADED
        else:
            observation.status = HealthStatus.HEALTHY
            
        return observation

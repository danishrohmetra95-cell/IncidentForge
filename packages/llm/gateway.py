import os
import json
import time
import logging
import asyncio
from typing import AsyncIterator, Any
from pydantic import BaseModel
from openai import AsyncOpenAI
from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError

logger = logging.getLogger(__name__)

class ModelGatewayUnavailable(RuntimeError):
    """Raised when no live model providers are configured."""

class ProviderConfig:
    def __init__(self, name: str, api_key: str, base_url: str | None, timeout: float = 60.0):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.client = AsyncOpenAI(
            api_key=api_key or f"missing-{name}-key",
            base_url=base_url,
            timeout=timeout,
        ) if api_key else None

class ModelGateway:
    def __init__(self, timeout: float = 60.0):
        from apps.api.config import settings
        self.providers = [
            ProviderConfig(
                "gemini",
                settings.GEMINI_API_KEY,
                "https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout
            ),
            ProviderConfig(
                "featherless",
                settings.FEATHERLESS_API_KEY,
                settings.FEATHERLESS_BASE_URL,
                timeout
            ),
            ProviderConfig(
                "grok",
                settings.XAI_API_KEY,
                "https://api.x.ai/v1",
                timeout
            )
        ]

    @property
    def is_configured(self) -> bool:
        return any(p.client is not None for p in self.providers)

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise ModelGatewayUnavailable("No providers are configured for live model reasoning.")

    @property
    def active_provider_name(self) -> str | None:
        for p in self.providers:
            if p.client is not None:
                return p.name
        return None

    async def _record_run(self, agent_name: str, model: str, provider: str, latency: float, tokens: int, status: str):
        logger.info(f"AgentRun: {agent_name} | Provider: {provider} | Model: {model} | Latency: {latency:.2f}s | Tokens: {tokens} | Status: {status}")

    async def _execute_with_retry(self, func, agent_name: str, model: str, *args, **kwargs):
        self._ensure_configured()
        retries = 2
        base_delay = 1.0
        
        last_exception = None
        for provider in self.providers:
            if not provider.client:
                continue
            
            for attempt in range(retries):
                start_time = time.time()
                try:
                    response = await func(provider.client, *args, model=model, **kwargs)
                    latency = time.time() - start_time
                    
                    tokens_used = getattr(response.usage, "total_tokens", 0) if hasattr(response, "usage") else 0
                    await self._record_run(agent_name, model, provider.name, latency, tokens_used, "success")
                    return response
                except (RateLimitError, APIConnectionError, APITimeoutError) as e:
                    latency = time.time() - start_time
                    logger.warning(f"Attempt {attempt + 1} failed for {provider.name}: {e}")
                    await self._record_run(agent_name, model, provider.name, latency, 0, "error")
                    last_exception = e
                    if attempt == retries - 1:
                        break  # exhaust retries for this provider, move to next
                    await asyncio.sleep(base_delay * (2 ** attempt))
                except Exception as e:
                    latency = time.time() - start_time
                    logger.warning(f"Provider {provider.name} failed with unrecoverable error: {e}")
                    await self._record_run(agent_name, model, provider.name, latency, 0, "error")
                    last_exception = e
                    break  # move to next provider
                    
        raise last_exception or ModelGatewayUnavailable("All live providers failed.")

    async def generate(self, messages: list[dict], model: str, temperature: float = 0.3, max_tokens: int = 2048, agent_name: str = "default") -> str:
        async def _call(client, **k):
            return await client.chat.completions.create(**k)
            
        response = await self._execute_with_retry(
            _call, agent_name, model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def structured_generate(self, messages: list[dict], model: str, output_schema: type[BaseModel], temperature: float = 0.2, max_tokens: int = 2048, agent_name: str = "default") -> BaseModel:
        async def _call(client, **k):
            return await client.chat.completions.create(**k)

        response = await self._execute_with_retry(
            _call, agent_name, model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        
        raw_content = response.choices[0].message.content
        from packages.llm.structured import StructuredOutputParser, output_validation_status
        parser = StructuredOutputParser()
        try:
            return parser.parse(raw_content, output_schema)
        except Exception:
            output_validation_status.set("failed")
            raise

    async def stream(self, messages: list[dict], model: str, agent_name: str = "default") -> AsyncIterator[str]:
        self._ensure_configured()
        
        for provider in self.providers:
            if not provider.client:
                continue
            start_time = time.time()
            try:
                stream = await provider.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    stream=True
                )
                # Stream doesn't easily retry mid-stream, so we just use the first available provider
                async def _stream_generator():
                    async for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                    latency = time.time() - start_time
                    await self._record_run(agent_name, model, provider.name, latency, 0, "success_stream")
                return _stream_generator()
            except Exception as e:
                latency = time.time() - start_time
                await self._record_run(agent_name, model, provider.name, latency, 0, "error_stream")
                logger.warning(f"Streaming failed for provider {provider.name}: {e}")
                continue
                
        raise ModelGatewayUnavailable("All live providers failed to stream.")

    async def list_models(self) -> list[dict]:
        self._ensure_configured()
        for provider in self.providers:
            if provider.client:
                try:
                    response = await provider.client.models.list()
                    return [{"id": model.id} for model in response.data]
                except Exception:
                    continue
        return []

    async def health_check(self) -> bool:
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception:
            return False

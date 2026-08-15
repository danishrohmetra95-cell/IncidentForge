import os
import json
import time
import logging
import asyncio
from typing import AsyncIterator
from pydantic import BaseModel
from openai import AsyncOpenAI
from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError

logger = logging.getLogger(__name__)

class ModelGatewayUnavailable(RuntimeError):
    """Raised when live model reasoning was requested without configuration."""

class ModelGateway:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 60.0):
        self.api_key = api_key if api_key is not None else os.getenv("FEATHERLESS_API_KEY", "")
        self.client = AsyncOpenAI(
            base_url=base_url or os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
            api_key=self.api_key or "missing-featherless-key",
            timeout=timeout,
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise ModelGatewayUnavailable("FEATHERLESS_API_KEY is not configured for live model reasoning.")

    async def _record_run(self, agent_name: str, model: str, latency: float, tokens: int, status: str):
        # Implementation for AgentRun recording
        logger.info(f"AgentRun: {agent_name} | Model: {model} | Latency: {latency:.2f}s | Tokens: {tokens} | Status: {status}")

    async def _execute_with_retry(self, func, agent_name: str, model: str, *args, **kwargs):
        retries = 3
        base_delay = 1.0
        
        for attempt in range(retries):
            start_time = time.time()
            try:
                response = await func(*args, model=model, **kwargs)
                latency = time.time() - start_time
                
                # estimate tokens roughly if not provided
                tokens_used = getattr(response.usage, "total_tokens", 0) if hasattr(response, "usage") else 0
                
                await self._record_run(agent_name, model, latency, tokens_used, "success")
                return response
            except (RateLimitError, APIConnectionError, APITimeoutError) as e:
                latency = time.time() - start_time
                logger.warning(f"Attempt {attempt + 1} failed for {model}: {e}")
                await self._record_run(agent_name, model, latency, 0, "error")
                
                if attempt == retries - 1:
                    raise
                
                await asyncio.sleep(base_delay * (2 ** attempt))
            except Exception as e:
                latency = time.time() - start_time
                await self._record_run(agent_name, model, latency, 0, "error")
                raise

    async def generate(self, messages: list[dict], model: str, temperature: float = 0.3, max_tokens: int = 2048, agent_name: str = "default") -> str:
        self._ensure_configured()
        async def _call(**k):
            return await self.client.chat.completions.create(**k)
            
        response = await self._execute_with_retry(
            _call, agent_name, model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def structured_generate(self, messages: list[dict], model: str, output_schema: type[BaseModel], temperature: float = 0.2, max_tokens: int = 2048, agent_name: str = "default") -> BaseModel:
        self._ensure_configured()
        # Fallback to json output parsing
        async def _call(**k):
            return await self.client.chat.completions.create(**k)

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
        start_time = time.time()
        try:
            stream = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            latency = time.time() - start_time
            await self._record_run(agent_name, model, latency, 0, "success_stream")
        except Exception as e:
            latency = time.time() - start_time
            await self._record_run(agent_name, model, latency, 0, "error_stream")
            raise

    async def list_models(self) -> list[dict]:
        self._ensure_configured()
        response = await self.client.models.list()
        return [{"id": model.id} for model in response.data]

    async def health_check(self) -> bool:
        try:
            await self.list_models()
            return True
        except Exception:
            return False

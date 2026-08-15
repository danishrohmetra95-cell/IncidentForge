import os
import logging
from packages.contracts.domain import ModelRole
from packages.llm.gateway import ModelGateway

logger = logging.getLogger(__name__)

class ModelRouter:
    def __init__(self, gateway: ModelGateway):
        self.gateway = gateway
        self._available_models = []

    async def discover_models(self):
        try:
            models = await self.gateway.list_models()
            self._available_models = [m["id"] for m in models]
        except Exception as e:
            logger.error(f"Failed to discover models: {e}")
            self._available_models = []

    async def resolve(self, role: ModelRole) -> str:
        if not self._available_models:
            await self.discover_models()

        # Check overrides
        if role == ModelRole.FAST_REASONING and os.getenv("FAST_MODEL"):
            return os.getenv("FAST_MODEL")
        if role == ModelRole.DEEP_REASONING and os.getenv("DEEP_MODEL"):
            return os.getenv("DEEP_MODEL")
        if role == ModelRole.SYNTHESIS and os.getenv("SYNTHESIS_MODEL"):
            return os.getenv("SYNTHESIS_MODEL")

        # Find preferred models
        preferred = []
        if role == ModelRole.DEEP_REASONING:
            preferred = [m for m in self._available_models if "Kimi-K2" in m or "kimi" in m.lower()]
        elif role == ModelRole.SYNTHESIS:
            preferred = [m for m in self._available_models if "glm" in m.lower()]
        elif role == ModelRole.FAST_REASONING:
            preferred = [m for m in self._available_models if ("llama" in m.lower() and "8b" in m.lower()) or ("qwen" in m.lower() and "7b" in m.lower())]

        if preferred:
            return preferred[0]

        # Fallback to any instruction tuned model
        instruct_models = [m for m in self._available_models if "instruct" in m.lower() or "chat" in m.lower()]
        if instruct_models:
            return instruct_models[0]

        # Ultimate fallback
        return self._available_models[0] if self._available_models else "gpt-3.5-turbo"

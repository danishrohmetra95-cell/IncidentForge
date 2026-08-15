from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        ...

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        ...

class LocalEmbeddingProvider(EmbeddingProvider):
    """Uses sentence-transformers all-MiniLM-L6-v2 for local embedding."""
    
    def __init__(self):
        self._model = None
        self._dimension = 384

    def _get_model(self):
        if self._model is None:
            # Lazy loading
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._model

    async def embed(self, text: str) -> List[float]:
        # SentenceTransformers encodes synchronously, but we can wrap it if needed.
        # For simplicity in this async wrapper:
        model = self._get_model()
        embedding = model.encode(text)
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        embeddings = model.encode(texts)
        return [emb.tolist() for emb in embeddings]

    @property
    def dimension(self) -> int:
        return self._dimension

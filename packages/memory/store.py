from typing import List, Optional
import math
from packages.contracts.domain import IncidentMemoryRecord, IncidentFingerprint

class IncidentMemoryStore:
    MIN_SIMILARITY = 0.3

    def __init__(self):
        # In-memory storage for now
        self._records: List[IncidentMemoryRecord] = []

    async def store(self, record: IncidentMemoryRecord):
        """Stores the record in the database with embedding."""
        self._records.append(record)

    async def find_similar(self, fingerprint: IncidentFingerprint, limit: int = 5) -> List[IncidentMemoryRecord]:
        """Finds similar incidents using cosine similarity."""
        """Use embeddings when both sides have them, otherwise structural similarity.

        The fallback is intentionally kept here so every caller (including the
        repository) gets identical ranking and minimum-match behaviour.
        """
        from packages.memory.fingerprint import IncidentFingerprinter

        fingerprinter = IncidentFingerprinter()
        scored_records: list[tuple[float, IncidentMemoryRecord]] = []
        for record in self._records:
            if not record.fingerprint:
                continue

            if fingerprint.embedding and record.fingerprint.embedding:
                sim = self._cosine_similarity(
                    fingerprint.embedding, record.fingerprint.embedding
                )
            else:
                sim = fingerprinter.similarity(fingerprint, record.fingerprint)

            if sim >= self.MIN_SIMILARITY:
                scored_records.append((sim, record))
            
        scored_records.sort(key=lambda x: x[0], reverse=True)
        return [record for score, record in scored_records[:limit]]

    async def get_by_incident(self, incident_id: str) -> Optional[IncidentMemoryRecord]:
        for record in self._records:
            if record.incident_id == incident_id:
                return record
        return None
        
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a * a for a in v1))
        magnitude2 = math.sqrt(sum(b * b for b in v2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

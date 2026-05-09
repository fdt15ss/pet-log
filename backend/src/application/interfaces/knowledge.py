from __future__ import annotations

from typing import Protocol

from domain.models import CareKnowledgeChunk, CareKnowledgeHit, CareKnowledgeSource


class CareKnowledgeRetrieverInterface(Protocol):
    def search(self, question: str, limit: int = 3) -> tuple[CareKnowledgeHit, ...]:
        raise NotImplementedError


class CareKnowledgeIngestionInterface(Protocol):
    def ingest(self, source: CareKnowledgeSource) -> tuple[CareKnowledgeChunk, ...]:
        raise NotImplementedError


class EmbeddingProviderInterface(Protocol):
    def embed(self, text: str) -> tuple[float, ...]:
        raise NotImplementedError

from __future__ import annotations

from domain.models import CareKnowledgeChunk, CareKnowledgeSource


class CareKnowledgeRepository:
    def save_source(self, source: CareKnowledgeSource) -> None:
        raise NotImplementedError

    def save_chunks(self, chunks: tuple[CareKnowledgeChunk, ...]) -> None:
        raise NotImplementedError

    def list_chunks(self) -> tuple[CareKnowledgeChunk, ...]:
        raise NotImplementedError

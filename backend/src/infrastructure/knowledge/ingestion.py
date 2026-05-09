from __future__ import annotations

from application.interfaces import CareKnowledgeIngestionInterface
from domain.models import CareKnowledgeChunk, CareKnowledgeSource


class UrlCareKnowledgeIngestor(CareKnowledgeIngestionInterface):
    def __init__(self, *, allowed_domains: tuple[str, ...]) -> None:
        self._allowed_domains = allowed_domains

    def ingest(self, source: CareKnowledgeSource) -> tuple[CareKnowledgeChunk, ...]:
        raise NotImplementedError

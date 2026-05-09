from __future__ import annotations

from application.interfaces import CareKnowledgeRetrieverInterface, EmbeddingProviderInterface
from domain.models import CareKnowledgeHit
from infrastructure.knowledge.repository import CareKnowledgeRepository


class CareKnowledgeRetriever(CareKnowledgeRetrieverInterface):
    def __init__(
        self,
        *,
        repository: CareKnowledgeRepository,
        embedding_provider: EmbeddingProviderInterface,
    ) -> None:
        self._repository = repository
        self._embedding_provider = embedding_provider

    def search(self, question: str, limit: int = 3) -> tuple[CareKnowledgeHit, ...]:
        raise NotImplementedError

from __future__ import annotations

from typing import Protocol

from domain.models import CareKnowledgeHit


class CareKnowledgeRetrieverInterface(Protocol):
    def search(self, question: str, limit: int = 3) -> tuple[CareKnowledgeHit, ...]:
        raise NotImplementedError

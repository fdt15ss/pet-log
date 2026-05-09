from __future__ import annotations

from domain.models import CareKnowledgeHit


class CareKnowledgeRetriever:
    def search(self, question: str, limit: int = 3) -> tuple[CareKnowledgeHit, ...]:
        return ()

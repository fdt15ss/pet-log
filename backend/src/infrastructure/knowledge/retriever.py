from __future__ import annotations

from domain.models import CareKnowledgeHit


class CareKnowledgeRetriever:
    def __init__(self, persist_directory: str | None = None) -> None:
        self._persist_directory = persist_directory

    def search(self, question: str, limit: int = 3) -> tuple[CareKnowledgeHit, ...]:
        return ()

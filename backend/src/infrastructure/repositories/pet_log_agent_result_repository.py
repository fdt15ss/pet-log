from __future__ import annotations

from application.dto import PetLogAgentResult


class PetLogAgentResultRepository:
    def get_latest(self, pet_id: str) -> PetLogAgentResult:
        raise NotImplementedError

from __future__ import annotations

from application.dto import PetLogAgentResult
from application.interfaces import PetLogAgentResultReaderInterface


class PetLogAgentResultRepository(PetLogAgentResultReaderInterface):
    def get_latest(self, pet_id: str) -> PetLogAgentResult:
        raise NotImplementedError

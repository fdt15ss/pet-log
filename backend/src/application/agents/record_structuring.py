from __future__ import annotations

from application.dto import PetLogAgentInput
from application.interfaces import RecordStructurerInterface, RecordStructuringAgentInterface
from domain.models import StructuredRecordCandidate


class RecordStructuringAgent(RecordStructuringAgentInterface):
    def __init__(self, structurer: RecordStructurerInterface) -> None:
        self._structurer = structurer

    def structure(self, input: PetLogAgentInput) -> StructuredRecordCandidate:
        return self._structurer.structure(input)

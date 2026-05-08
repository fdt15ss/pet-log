from __future__ import annotations

from application.dto import PetLogAgentInput
from application.interfaces import RecordStructurerInterface, RecordStructuringAgentInterface
from domain.models import StructuredRecordBatch


class RecordStructuringAgent(RecordStructuringAgentInterface):
    def __init__(self, structurer: RecordStructurerInterface) -> None:
        self._structurer = structurer

    def structure(self, input: PetLogAgentInput) -> StructuredRecordBatch:
        return self._structurer.structure(input)

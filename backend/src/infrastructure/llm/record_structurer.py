from __future__ import annotations

from application.dto import PetLogAgentInput
from application.interfaces import RecordStructurerInterface
from domain.models import StructuredRecordBatch


class RecordStructurer(RecordStructurerInterface):
    def structure(self, input: PetLogAgentInput) -> StructuredRecordBatch:
        raise NotImplementedError

from __future__ import annotations

from application.interfaces import MissingRecordPolicyInterface
from domain.models import CareInsight, PetProfile, PetRecord


class MissingRecordPolicy(MissingRecordPolicyInterface):
    def detect_missing_records(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> tuple[CareInsight, ...]:
        return ()

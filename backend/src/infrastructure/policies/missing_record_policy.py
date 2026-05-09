from __future__ import annotations

from domain.models import CareInsight, PetProfile, PetRecord


class MissingRecordPolicy:
    def detect_missing_records(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> tuple[CareInsight, ...]:
        return ()

from __future__ import annotations

from domain.models import CareInsight, PetProfile, PetRecord


class PatternAnalyzer:
    def analyze(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> tuple[CareInsight, ...]:
        return ()

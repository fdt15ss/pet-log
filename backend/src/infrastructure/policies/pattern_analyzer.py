from __future__ import annotations

from application.interfaces import PatternAnalyzerInterface
from domain.models import CareInsight, PetProfile, PetRecord


class PatternAnalyzer(PatternAnalyzerInterface):
    def analyze(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> tuple[CareInsight, ...]:
        return ()

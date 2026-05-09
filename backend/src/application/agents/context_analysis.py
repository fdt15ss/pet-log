from __future__ import annotations

from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder


class ContextAnalysisAgent:
    def __init__(
        self,
        pattern_analyzer,
        missing_record_policy,
    ) -> None:
        self._pattern_analyzer = pattern_analyzer
        self._missing_record_policy = missing_record_policy

    def analyze(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> ContextAnalysisResult:
        insights = self._pattern_analyzer.analyze(pet, records)
        missing_record_insights = self._missing_record_policy.detect_missing_records(pet, records)
        return ContextAnalysisResult(
            insights=insights,
            missing_record_insights=missing_record_insights,
        )

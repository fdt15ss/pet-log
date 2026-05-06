from __future__ import annotations

from application.interfaces import ContextAnalysisAgentInterface, MissingRecordPolicyInterface, PatternAnalyzerInterface
from domain.models import CareInsight, ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder


class ContextAnalysisAgent(ContextAnalysisAgentInterface):
    def __init__(
        self,
        pattern_analyzer: PatternAnalyzerInterface,
        missing_record_policy: MissingRecordPolicyInterface,
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

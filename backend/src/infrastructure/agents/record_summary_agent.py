from __future__ import annotations

from application.dto import RecordSummaryResult
from application.interfaces import RecordSummaryAgentInterface
from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder


class RecordSummaryAgent(RecordSummaryAgentInterface):
    def summarize(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> RecordSummaryResult:
        raise NotImplementedError

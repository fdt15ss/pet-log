from __future__ import annotations

from application.dto import RecordSummaryResult
from application.interfaces import RecordSummaryAgentInterface, RecordSummaryProviderInterface
from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder


class RecordSummaryAgent(RecordSummaryAgentInterface):
    def __init__(self, summary_provider: RecordSummaryProviderInterface) -> None:
        self._summary_provider = summary_provider

    def summarize(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> RecordSummaryResult:
        return self._summary_provider.summarize(pet, records, context, due_items)

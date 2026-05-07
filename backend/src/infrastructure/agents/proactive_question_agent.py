from __future__ import annotations

from application.dto import ProactiveQuestionResult
from application.interfaces import ProactiveQuestionAgentInterface
from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder


class ProactiveQuestionAgent(ProactiveQuestionAgentInterface):
    def build_question(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> ProactiveQuestionResult | None:
        raise NotImplementedError

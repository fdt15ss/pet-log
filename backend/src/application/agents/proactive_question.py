from __future__ import annotations

from application.dto import ProactiveQuestionResult
from application.interfaces import ProactiveQuestionAgentInterface, ProactiveQuestionPolicyInterface
from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder


class ProactiveQuestionAgent(ProactiveQuestionAgentInterface):
    def __init__(self, question_policy: ProactiveQuestionPolicyInterface) -> None:
        self._question_policy = question_policy

    def build_question(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> ProactiveQuestionResult | None:
        return self._question_policy.build_question(pet, records, context, due_items)

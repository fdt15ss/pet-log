from __future__ import annotations

from application.interfaces import CauseHypothesisPolicyInterface
from domain.models import CareInsight, ContextAnalysisResult, PetProfile, PetRecord


class CauseHypothesisPolicy(CauseHypothesisPolicyInterface):
    def analyze(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
    ) -> tuple[CareInsight, ...]:
        raise NotImplementedError

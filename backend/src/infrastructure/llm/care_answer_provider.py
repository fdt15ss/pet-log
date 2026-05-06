from __future__ import annotations

from application.interfaces import CareAnswerProviderInterface
from domain.models import CareContext


class CareAnswerProvider(CareAnswerProviderInterface):
    def answer(self, context: CareContext, question: str) -> str:
        raise NotImplementedError

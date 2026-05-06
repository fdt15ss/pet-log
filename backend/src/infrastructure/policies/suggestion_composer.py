from __future__ import annotations

from application.interfaces import SuggestionComposerInterface
from domain.models import CareInsight, CareSuggestion, PetProfile


class SuggestionComposer(SuggestionComposerInterface):
    def compose(self, pet: PetProfile, insights: tuple[CareInsight, ...]) -> tuple[CareSuggestion, ...]:
        raise NotImplementedError

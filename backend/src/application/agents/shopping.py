from __future__ import annotations

from domain.models import PetProfile, PetRecord, ShoppingRecommendation


class ShoppingAgent:
    def __init__(self, recommendation_provider) -> None:
        self._recommendation_provider = recommendation_provider

    def recommend(
        self,
        pet: PetProfile,
        text: str,
        records: tuple[PetRecord, ...],
    ) -> tuple[ShoppingRecommendation, ...]:
        return self._recommendation_provider.recommend(pet, text, records)

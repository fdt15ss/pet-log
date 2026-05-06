from __future__ import annotations

from application.interfaces import PetProfileReaderInterface
from domain.models import PetProfile


class PetProfileRepository(PetProfileReaderInterface):
    def __init__(self, pets: tuple[PetProfile, ...] = ()) -> None:
        self._pets_by_id = {pet.id: pet for pet in pets}

    def get_pet(self, pet_id: str) -> PetProfile:
        return self._pets_by_id[pet_id]

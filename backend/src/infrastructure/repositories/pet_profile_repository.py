from __future__ import annotations

import json
import sqlite3

from application.interfaces import PetProfileReaderInterface
from domain.models import PetProfile
from infrastructure.database import initialize_schema


class PetProfileRepository(PetProfileReaderInterface):
    def __init__(self, pets: tuple[PetProfile, ...] = (), connection: sqlite3.Connection | None = None) -> None:
        self._connection = connection
        if self._connection is not None:
            initialize_schema(self._connection)
        self._pets_by_id = {pet.id: pet for pet in pets}

    def get_pet(self, pet_id: str) -> PetProfile:
        if self._connection is not None:
            row = self._connection.execute(
                """
                SELECT id, name, breed, species, age_label, personality, notes
                FROM pets
                WHERE id = ? AND deleted_at IS NULL
                """,
                (pet_id,),
            ).fetchone()
            if row is None:
                raise KeyError(pet_id)
            return PetProfile(
                id=row["id"],
                name=row["name"],
                breed=row["breed"],
                species=row["species"],
                age_label=row["age_label"],
                personality=row["personality"],
                notes=tuple(json.loads(row["notes"])),
            )

        return self._pets_by_id[pet_id]

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace

from domain.models import PetProfile
from infrastructure.database import initialize_schema


class PetProfileRepository:
    def __init__(self, pets: tuple[PetProfile, ...] = (), connection: sqlite3.Connection | None = None) -> None:
        self._connection = connection
        if self._connection is not None:
            initialize_schema(self._connection)
        self._pets_by_id = {pet.id: pet for pet in pets}

    def get_pet(self, pet_id: str) -> PetProfile:
        if self._connection is not None:
            row = self._connection.execute(
                """
                SELECT id, name, breed, species, age_label, sex_label, weight_label, birthday, personality, notes, photo_file_id
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
                sex_label=row["sex_label"],
                weight_label=row["weight_label"],
                birthday=row["birthday"],
                personality=row["personality"],
                notes=tuple(json.loads(row["notes"])),
                photo_file_id=row["photo_file_id"],
            )

        return self._pets_by_id[pet_id]

    def set_profile_photo_file(self, pet_id: str, file_id: str) -> None:
        if self._connection is None:
            self._pets_by_id[pet_id] = replace(self._pets_by_id[pet_id], photo_file_id=file_id)
            return

        cursor = self._connection.execute(
            """
            UPDATE pets
            SET photo_file_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND deleted_at IS NULL
            """,
            (file_id, pet_id),
        )
        if cursor.rowcount == 0:
            raise KeyError(pet_id)
        self._connection.commit()

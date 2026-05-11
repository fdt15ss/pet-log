from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from domain.models import CareSchedule, PlannedReminder
from infrastructure.database import initialize_schema


class ScheduleRepository:
    def __init__(
        self,
        due_items_by_pet_id: dict[str, tuple[PlannedReminder, ...]] | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._connection = connection
        if self._connection is not None:
            initialize_schema(self._connection)
        self._due_items_by_pet_id = due_items_by_pet_id or {}

    def list_due_items(self, pet_id: str, days_ahead: int) -> tuple[PlannedReminder, ...]:
        if self._connection is not None:
            max_due_date = (datetime.now(UTC).date() + timedelta(days=days_ahead)).isoformat()
            rows = self._connection.execute(
                """
                SELECT title, due_date, note, repeat_label
                FROM care_schedules
                WHERE pet_id = ?
                    AND deleted_at IS NULL
                    AND is_done = 0
                    AND due_date <= ?
                ORDER BY due_date, created_at
                """,
                (pet_id, max_due_date),
            ).fetchall()
            return tuple(
                PlannedReminder(
                    title=row["title"],
                    due_date=row["due_date"],
                    reason=row["note"] or row["repeat_label"],
                )
                for row in rows
            )

        return self._due_items_by_pet_id.get(pet_id, ())

    def list_for_pet(self, pet_id: str) -> tuple[CareSchedule, ...]:
        if self._connection is not None:
            rows = self._connection.execute(
                """
                SELECT id, pet_id, category, title, due_date, repeat_label, note, is_done
                FROM care_schedules
                WHERE pet_id = ? AND deleted_at IS NULL
                ORDER BY due_date, created_at
                """,
                (pet_id,),
            ).fetchall()
            return tuple(
                CareSchedule(
                    id=row["id"],
                    pet_id=row["pet_id"],
                    category=row["category"],
                    title=row["title"],
                    due_date=row["due_date"],
                    repeat_label=row["repeat_label"],
                    note=row["note"],
                    is_done=bool(row["is_done"]),
                )
                for row in rows
            )

        return ()

from __future__ import annotations

from application.interfaces import ScheduleContextReaderInterface
from domain.models import PlannedReminder


class ScheduleRepository(ScheduleContextReaderInterface):
    def __init__(self, due_items_by_pet_id: dict[str, tuple[PlannedReminder, ...]] | None = None) -> None:
        self._due_items_by_pet_id = due_items_by_pet_id or {}

    def list_due_items(self, pet_id: str, days_ahead: int) -> tuple[PlannedReminder, ...]:
        return self._due_items_by_pet_id.get(pet_id, ())

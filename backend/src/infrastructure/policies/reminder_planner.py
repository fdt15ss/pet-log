from __future__ import annotations

from application.interfaces import ReminderPlannerInterface
from domain.models import PetProfile, PetRecord, PlannedReminder


class ReminderPlanner(ReminderPlannerInterface):
    def plan(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[PlannedReminder, ...]:
        raise NotImplementedError

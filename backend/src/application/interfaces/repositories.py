from __future__ import annotations

from typing import Protocol

from application.dto import PetLogAgentResult
from domain.models import PetProfile, PetRecord, PlannedReminder, StructuredRecordCandidate


class PetProfileReaderInterface(Protocol):
    def get_pet(self, pet_id: str) -> PetProfile:
        raise NotImplementedError


class RecordHistoryReaderInterface(Protocol):
    def list_recent(self, pet_id: str, lookback_days: int) -> tuple[PetRecord, ...]:
        raise NotImplementedError

    def list_by_ids(self, pet_id: str, record_ids: tuple[str, ...]) -> tuple[PetRecord, ...]:
        raise NotImplementedError


class RecordRepositoryInterface(Protocol):
    def save_candidate(self, pet_id: str, candidate: StructuredRecordCandidate) -> PetRecord:
        raise NotImplementedError


class ScheduleContextReaderInterface(Protocol):
    def list_due_items(self, pet_id: str, days_ahead: int) -> tuple[PlannedReminder, ...]:
        raise NotImplementedError


class PetLogAgentResultReaderInterface(Protocol):
    def get_latest(self, pet_id: str) -> PetLogAgentResult:
        raise NotImplementedError

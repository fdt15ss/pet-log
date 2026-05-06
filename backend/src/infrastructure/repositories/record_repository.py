from __future__ import annotations

from application.interfaces import RecordHistoryReaderInterface, RecordRepositoryInterface
from domain.models import PetRecord, StructuredRecordCandidate


class RecordRepository(RecordHistoryReaderInterface, RecordRepositoryInterface):
    def __init__(self, records: tuple[PetRecord, ...] = ()) -> None:
        self._records = list(records)

    def list_recent(self, pet_id: str, lookback_days: int) -> tuple[PetRecord, ...]:
        return tuple(record for record in self._records if record.pet_id == pet_id)

    def list_by_ids(self, pet_id: str, record_ids: tuple[str, ...]) -> tuple[PetRecord, ...]:
        records_by_id = {record.id: record for record in self._records if record.pet_id == pet_id}
        return tuple(records_by_id[record_id] for record_id in record_ids if record_id in records_by_id)

    def save_candidate(self, pet_id: str, candidate: StructuredRecordCandidate) -> PetRecord:
        record = PetRecord(
            id=f"record-{len(self._records) + 1}",
            pet_id=pet_id,
            category=candidate.category,
            title=candidate.title,
            detail=candidate.detail,
            status=candidate.status,
            recorded_at="",
            source="ai_preview",
        )
        self._records.append(record)
        return record

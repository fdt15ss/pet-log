from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from application.interfaces import RecordHistoryReaderInterface, RecordRepositoryInterface
from domain.enums import RecordInputSource
from domain.models import PetRecord, StructuredRecordCandidate
from infrastructure.database import initialize_schema


class RecordRepository(RecordHistoryReaderInterface, RecordRepositoryInterface):
    def __init__(self, records: tuple[PetRecord, ...] = (), connection: sqlite3.Connection | None = None) -> None:
        self._connection = connection
        if self._connection is not None:
            initialize_schema(self._connection)
        self._records = list(records)

    def list_recent(self, pet_id: str, lookback_days: int) -> tuple[PetRecord, ...]:
        if self._connection is not None:
            rows = self._connection.execute(
                """
                SELECT id, pet_id, category, title, detail, status, recorded_at, source
                FROM pet_records
                WHERE pet_id = ? AND deleted_at IS NULL
                ORDER BY recorded_at, created_at
                """,
                (pet_id,),
            ).fetchall()
            return tuple(_record_from_row(row) for row in rows)

        return tuple(record for record in self._records if record.pet_id == pet_id)

    def list_by_ids(self, pet_id: str, record_ids: tuple[str, ...]) -> tuple[PetRecord, ...]:
        if self._connection is not None:
            if not record_ids:
                return ()

            placeholders = ", ".join("?" for _ in record_ids)
            rows = self._connection.execute(
                f"""
                SELECT id, pet_id, category, title, detail, status, recorded_at, source
                FROM pet_records
                WHERE pet_id = ? AND deleted_at IS NULL AND id IN ({placeholders})
                """,
                (pet_id, *record_ids),
            ).fetchall()
            records_by_id = {row["id"]: _record_from_row(row) for row in rows}
            return tuple(records_by_id[record_id] for record_id in record_ids if record_id in records_by_id)

        records_by_id = {record.id: record for record in self._records if record.pet_id == pet_id}
        return tuple(records_by_id[record_id] for record_id in record_ids if record_id in records_by_id)

    def save_candidate(
        self,
        pet_id: str,
        candidate: StructuredRecordCandidate,
        source: RecordInputSource = "ai_preview",
    ) -> PetRecord:
        if self._connection is not None:
            record = PetRecord(
                id=str(uuid4()),
                pet_id=pet_id,
                category=candidate.category,
                title=candidate.title,
                detail=candidate.detail,
                status=candidate.status,
                recorded_at=_utc_now(),
                source=source,
            )
            self._connection.execute(
                """
                INSERT INTO pet_records (id, pet_id, category, title, detail, status, recorded_at, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.pet_id,
                    record.category,
                    record.title,
                    record.detail,
                    record.status,
                    record.recorded_at,
                    record.source,
                ),
            )
            self._connection.commit()
            return record

        record = PetRecord(
            id=f"record-{len(self._records) + 1}",
            pet_id=pet_id,
            category=candidate.category,
            title=candidate.title,
            detail=candidate.detail,
            status=candidate.status,
            recorded_at="",
            source=source,
        )
        self._records.append(record)
        return record


def _record_from_row(row: sqlite3.Row) -> PetRecord:
    return PetRecord(
        id=row["id"],
        pet_id=row["pet_id"],
        category=row["category"],
        title=row["title"],
        detail=row["detail"],
        status=row["status"],
        recorded_at=row["recorded_at"],
        source=row["source"],
    )


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

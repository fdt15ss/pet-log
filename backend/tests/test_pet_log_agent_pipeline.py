from __future__ import annotations

import unittest

from application.dto import PetLogAgentInput
from application.pipelines.pet_log_agent import PetLogAgentPipeline
from domain.models import (
    ContextAnalysisResult,
    PetProfile,
    PetRecord,
    PlannedReminder,
    StructuredRecordBatch,
    StructuredRecordCandidate,
)


class FakeRecordStructuringAgent:
    def __init__(self, batch: StructuredRecordBatch) -> None:
        self._batch = batch

    def structure(self, input: PetLogAgentInput) -> StructuredRecordBatch:
        return self._batch


class FakeRecordRepository:
    def __init__(self) -> None:
        self.saved_candidates: list[StructuredRecordCandidate] = []

    def list_recent(self, pet_id: str, lookback_days: int) -> tuple[PetRecord, ...]:
        return ()

    def list_by_ids(self, pet_id: str, record_ids: tuple[str, ...]) -> tuple[PetRecord, ...]:
        return ()

    def save_candidate(self, pet_id: str, candidate: StructuredRecordCandidate) -> PetRecord:
        self.saved_candidates.append(candidate)
        return PetRecord(
            id=f"record-{len(self.saved_candidates)}",
            pet_id=pet_id,
            category=candidate.category,
            title=candidate.title,
            detail=candidate.detail,
            status=candidate.status,
            recorded_at="2026-05-08T09:00:00Z",
            source="ai_preview",
        )


class FakeScheduleContextReader:
    def list_due_items(self, pet_id: str, days_ahead: int) -> tuple[PlannedReminder, ...]:
        return ()


class FakeContextAnalysisAgent:
    def analyze(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> ContextAnalysisResult:
        return ContextAnalysisResult()


class FakeRiskDetectionAgent:
    def detect(self, text: str, records: tuple[PetRecord, ...]) -> tuple[object, ...]:
        return ()


class FakeSuggestionAgent:
    def suggest(
        self,
        pet: PetProfile,
        context: ContextAnalysisResult,
        safety_notices: tuple[object, ...],
    ) -> tuple[object, ...]:
        return ()


class FakeReminderAgent:
    def __init__(self) -> None:
        self.records: tuple[PetRecord, ...] = ()

    def plan(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[PlannedReminder, ...]:
        self.records = records
        return ()


class TestPetLogAgentPipeline(unittest.TestCase):
    def test_saves_each_candidate_from_structured_record_batch(self) -> None:
        meal = StructuredRecordCandidate(
            title="식사",
            detail="밥을 조금 먹음",
            category="meal",
            status="notice",
            confidence=0.86,
            needs_confirmation=False,
        )
        walk = StructuredRecordCandidate(
            title="산책",
            detail="산책을 하지 못함",
            category="walk",
            status="notice",
            confidence=0.84,
            needs_confirmation=False,
        )
        batch = StructuredRecordBatch(candidates=(meal, walk))
        repository = FakeRecordRepository()
        reminder_agent = FakeReminderAgent()
        pipeline = self._pipeline(batch, repository, reminder_agent)

        result = pipeline.handle(
            PetLogAgentInput(
                pet=PetProfile(id="pet-1", name="초코"),
                text="오늘 밥을 조금 먹고 산책은 못 했어",
                source="manual",
            )
        )

        self.assertEqual(result.candidates, (meal, walk))
        self.assertEqual(tuple(record.title for record in result.saved_records), ("식사", "산책"))
        self.assertEqual(repository.saved_candidates, [meal, walk])
        self.assertEqual(tuple(record.title for record in reminder_agent.records), ("식사", "산책"))

    def test_confirmation_required_batch_does_not_save_records_without_confirm(self) -> None:
        candidate = StructuredRecordCandidate(
            title="식사",
            detail="밥을 거의 먹지 않음",
            category="meal",
            status="alert",
            confidence=0.7,
            needs_confirmation=True,
        )
        repository = FakeRecordRepository()
        pipeline = self._pipeline(StructuredRecordBatch(candidates=(candidate,)), repository)

        result = pipeline.handle(
            PetLogAgentInput(
                pet=PetProfile(id="pet-1", name="초코"),
                text="오늘 밥을 거의 안 먹었어",
                source="manual",
            )
        )

        self.assertEqual(result.candidates, (candidate,))
        self.assertEqual(result.saved_records, ())
        self.assertEqual(repository.saved_candidates, [])

    def _pipeline(
        self,
        batch: StructuredRecordBatch,
        repository: FakeRecordRepository,
        reminder_agent: FakeReminderAgent | None = None,
    ) -> PetLogAgentPipeline:
        reminder_agent = reminder_agent or FakeReminderAgent()
        return PetLogAgentPipeline(
            record_structuring_agent=FakeRecordStructuringAgent(batch),
            record_history_reader=repository,
            schedule_context_reader=FakeScheduleContextReader(),
            context_analysis_agent=FakeContextAnalysisAgent(),
            risk_detection_agent=FakeRiskDetectionAgent(),
            record_repository=repository,
            suggestion_agent=FakeSuggestionAgent(),
            reminder_agent=reminder_agent,
        )


if __name__ == "__main__":
    unittest.main()

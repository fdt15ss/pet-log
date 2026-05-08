from __future__ import annotations

from typing import Protocol

from application.dto import NotificationCandidate, PetLogAgentInput, ProactiveQuestionResult, RecordSummaryResult
from domain.models import (
    CareContext,
    CareSuggestion,
    ContextAnalysisResult,
    PetProfile,
    PetRecord,
    PlannedReminder,
    SafetyNotice,
    StructuredRecordBatch,
    StructuredRecordCandidate,
)


class RecordStructuringAgentInterface(Protocol):
    def structure(self, input: PetLogAgentInput) -> StructuredRecordBatch:
        raise NotImplementedError


class ContextAnalysisAgentInterface(Protocol):
    def analyze(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> ContextAnalysisResult:
        raise NotImplementedError


class RiskDetectionAgentInterface(Protocol):
    def detect(self, text: str, records: tuple[PetRecord, ...]) -> tuple[SafetyNotice, ...]:
        raise NotImplementedError


class SuggestionAgentInterface(Protocol):
    def suggest(
        self,
        pet: PetProfile,
        context: ContextAnalysisResult,
        safety_notices: tuple[SafetyNotice, ...],
    ) -> tuple[CareSuggestion, ...]:
        raise NotImplementedError


class ReminderAgentInterface(Protocol):
    def plan(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[PlannedReminder, ...]:
        raise NotImplementedError


class RecordSummaryAgentInterface(Protocol):
    def summarize(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> RecordSummaryResult:
        raise NotImplementedError


class ProactiveQuestionAgentInterface(Protocol):
    def build_question(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> ProactiveQuestionResult | None:
        raise NotImplementedError


class NotificationAgentInterface(Protocol):
    def plan(
        self,
        pet: PetProfile,
        context: ContextAnalysisResult,
        safety_notices: tuple[SafetyNotice, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[NotificationCandidate, ...]:
        raise NotImplementedError


class PhotoRecordUnderstandingAgentInterface(Protocol):
    def understand(
        self,
        pet: PetProfile,
        image: bytes,
        content_type: str,
        user_note: str | None = None,
    ) -> StructuredRecordCandidate:
        raise NotImplementedError


class CareContextBuilderInterface(Protocol):
    def build(self, pet_id: str, lookback_days: int) -> CareContext:
        raise NotImplementedError


class PetPersonaAgentInterface(Protocol):
    def respond(self, context: CareContext, message: str) -> str:
        raise NotImplementedError

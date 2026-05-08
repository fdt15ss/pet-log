from __future__ import annotations

from typing import Protocol

from application.dto import PetLogAgentInput, RecordSummaryResult
from domain.models import (
    CareContext,
    ContextAnalysisResult,
    PetProfile,
    PetRecord,
    PlannedReminder,
    StructuredRecordBatch,
    StructuredRecordCandidate,
)


class RecordStructurerInterface(Protocol):
    def structure(self, input: PetLogAgentInput) -> StructuredRecordBatch:
        raise NotImplementedError


class RecordSummaryProviderInterface(Protocol):
    def summarize(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> RecordSummaryResult:
        raise NotImplementedError


class CareAnswerProviderInterface(Protocol):
    def answer(self, context: CareContext, question: str) -> str:
        raise NotImplementedError


class PetPersonaResponderInterface(Protocol):
    def respond(self, context: CareContext, message: str) -> str:
        raise NotImplementedError


class ImageRecordUnderstandingProviderInterface(Protocol):
    def understand(
        self,
        pet: PetProfile,
        image: bytes,
        content_type: str,
        user_note: str | None = None,
    ) -> StructuredRecordCandidate:
        raise NotImplementedError


class SpeechToTextInterface(Protocol):
    def transcribe(self, audio: bytes, content_type: str) -> str:
        raise NotImplementedError


class TextToSpeechInterface(Protocol):
    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        raise NotImplementedError

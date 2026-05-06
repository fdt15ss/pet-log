from __future__ import annotations

from typing import Protocol

from application.dto import PetLogAgentInput
from domain.models import CareContext, StructuredRecordCandidate


class RecordStructurerInterface(Protocol):
    def structure(self, input: PetLogAgentInput) -> StructuredRecordCandidate:
        raise NotImplementedError


class CareAnswerProviderInterface(Protocol):
    def answer(self, context: CareContext, question: str) -> str:
        raise NotImplementedError


class PetPersonaResponderInterface(Protocol):
    def respond(self, context: CareContext, message: str) -> str:
        raise NotImplementedError


class SpeechToTextInterface(Protocol):
    def transcribe(self, audio: bytes, content_type: str) -> str:
        raise NotImplementedError


class TextToSpeechInterface(Protocol):
    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        raise NotImplementedError

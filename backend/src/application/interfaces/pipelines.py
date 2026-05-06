from __future__ import annotations

from typing import Protocol

from application.dto import (
    CareQuestionResult,
    HomeFeedResult,
    HospitalSummaryResult,
    PetChatResult,
    PetLogAgentInput,
    PetLogAgentResult,
)


class PetLogAgentPipelineInterface(Protocol):
    def handle(self, input: PetLogAgentInput) -> PetLogAgentResult:
        raise NotImplementedError


class HomeFeedPipelineInterface(Protocol):
    def build(self, pet_id: str) -> HomeFeedResult:
        raise NotImplementedError


class CareQuestionPipelineInterface(Protocol):
    def ask(self, pet_id: str, question: str) -> CareQuestionResult:
        raise NotImplementedError


class PetChatPipelineInterface(Protocol):
    def chat(self, pet_id: str, message: str) -> PetChatResult:
        raise NotImplementedError


class HospitalSummaryPipelineInterface(Protocol):
    def summarize(self, pet_id: str, record_ids: tuple[str, ...]) -> HospitalSummaryResult:
        raise NotImplementedError

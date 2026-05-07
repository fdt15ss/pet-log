from __future__ import annotations

from typing import Protocol

from application.dto import HomeFeedResult, HospitalSummaryResult, PetLogAgentResult, RecordSummaryResult
from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder


class HomeFeedComposerInterface(Protocol):
    def compose(
        self,
        pet: PetProfile,
        agent_result: PetLogAgentResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> HomeFeedResult:
        raise NotImplementedError


class RecordSummaryComposerInterface(Protocol):
    def compose(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> RecordSummaryResult:
        raise NotImplementedError


class HospitalReportComposerInterface(Protocol):
    def compose(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> HospitalSummaryResult:
        raise NotImplementedError

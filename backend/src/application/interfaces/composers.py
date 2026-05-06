from __future__ import annotations

from typing import Protocol

from application.dto import HomeFeedResult, HospitalSummaryResult, PetLogAgentResult
from domain.models import PetProfile, PetRecord, PlannedReminder


class HomeFeedComposerInterface(Protocol):
    def compose(
        self,
        pet: PetProfile,
        agent_result: PetLogAgentResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> HomeFeedResult:
        raise NotImplementedError


class HospitalReportComposerInterface(Protocol):
    def compose(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> HospitalSummaryResult:
        raise NotImplementedError

from __future__ import annotations

from typing import Protocol

from domain.models import CareInsight, CareSuggestion, PetProfile, PetRecord, PlannedReminder, SafetyNotice


class PatternAnalyzerInterface(Protocol):
    def analyze(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> tuple[CareInsight, ...]:
        raise NotImplementedError


class MissingRecordPolicyInterface(Protocol):
    def detect_missing_records(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> tuple[CareInsight, ...]:
        raise NotImplementedError


class RiskSignalPolicyInterface(Protocol):
    def detect_risks(self, text: str, records: tuple[PetRecord, ...]) -> tuple[SafetyNotice, ...]:
        raise NotImplementedError


class SuggestionComposerInterface(Protocol):
    def compose(self, pet: PetProfile, insights: tuple[CareInsight, ...]) -> tuple[CareSuggestion, ...]:
        raise NotImplementedError


class ReminderPlannerInterface(Protocol):
    def plan(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[PlannedReminder, ...]:
        raise NotImplementedError


class SafetyGuardInterface(Protocol):
    def check(self, text: str) -> SafetyNotice | None:
        raise NotImplementedError

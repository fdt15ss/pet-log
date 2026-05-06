from __future__ import annotations

from dataclasses import dataclass, field

from domain.models import (
    CareInsight,
    CareSuggestion,
    ContextAnalysisResult,
    PetProfile,
    PetRecord,
    PlannedReminder,
    SafetyNotice,
    StructuredRecordCandidate,
)


@dataclass(frozen=True)
class PetLogAgentInput:
    pet: PetProfile
    text: str
    source: str
    confirm: bool = False


@dataclass(frozen=True)
class PetLogAgentResult:
    candidate: StructuredRecordCandidate
    saved_record: PetRecord | None = None
    context_analysis: ContextAnalysisResult | None = None
    safety_notices: tuple[SafetyNotice, ...] = field(default_factory=tuple)
    suggestions: tuple[CareSuggestion, ...] = field(default_factory=tuple)
    reminders: tuple[PlannedReminder, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HomeFeedResult:
    today_summary: str
    recent_changes: tuple[str, ...] = ()
    alerts: tuple[CareInsight, ...] = ()
    suggestion_cards: tuple[CareSuggestion, ...] = ()
    reminders: tuple[PlannedReminder, ...] = ()


@dataclass(frozen=True)
class CareQuestionResult:
    answer: str
    safety_notice: SafetyNotice | None = None
    referenced_record_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PetChatResult:
    answer: str
    routed_to_care_question: bool = False
    safety_notice: SafetyNotice | None = None


@dataclass(frozen=True)
class HospitalSummaryResult:
    summary: str
    record_ids: tuple[str, ...] = ()
    safety_notice: SafetyNotice | None = None

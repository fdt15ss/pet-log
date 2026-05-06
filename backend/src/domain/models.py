from __future__ import annotations

from dataclasses import dataclass

from domain.enums import InsightSeverity, RecordCategory, RecordInputSource, RecordStatus


@dataclass(frozen=True)
class PetProfile:
    id: str
    name: str
    breed: str | None = None
    species: str | None = None
    age_label: str | None = None
    personality: str | None = None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class PetRecord:
    id: str
    pet_id: str
    category: RecordCategory
    title: str
    detail: str
    status: RecordStatus
    recorded_at: str
    source: RecordInputSource


@dataclass(frozen=True)
class StructuredRecordCandidate:
    title: str
    detail: str
    category: RecordCategory
    status: RecordStatus
    confidence: float
    needs_confirmation: bool
    measurements: tuple[str, ...] = ()


@dataclass(frozen=True)
class CareInsight:
    severity: InsightSeverity
    title: str
    reason: str
    source_record_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextAnalysisResult:
    insights: tuple[CareInsight, ...] = ()
    missing_record_insights: tuple[CareInsight, ...] = ()


@dataclass(frozen=True)
class CareSuggestion:
    title: str
    action: str
    reason: str
    source_record_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlannedReminder:
    title: str
    due_date: str
    reason: str


@dataclass(frozen=True)
class SafetyNotice:
    level: InsightSeverity
    message: str


@dataclass(frozen=True)
class CareContext:
    pet: PetProfile
    recent_records: tuple[PetRecord, ...] = ()
    due_reminders: tuple[PlannedReminder, ...] = ()

from __future__ import annotations

from dataclasses import dataclass

from domain.enums import (
    CommunityBoard,
    CommunityFeed,
    CommunityReactionType,
    FilePurpose,
    InsightSeverity,
    RecordCategory,
    RecordInputSource,
    RecordStatus,
)


@dataclass(frozen=True)
class PetProfile:
    id: str
    name: str
    breed: str | None = None
    species: str | None = None
    age_label: str | None = None
    sex_label: str | None = None
    weight_label: str | None = None
    birthday: str | None = None
    personality: str | None = None
    notes: tuple[str, ...] = ()
    photo_file_id: str | None = None


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
class StoredFile:
    id: str
    owner_user_id: str
    pet_id: str | None
    purpose: FilePurpose
    storage_key: str
    mime_type: str
    byte_size: int
    created_at: str | None = None


@dataclass(frozen=True)
class CommunityPost:
    id: str
    board: CommunityBoard
    title: str
    body: str
    author_name: str
    created_at: str
    comments: int = 0
    likes: int = 0
    distance: str | None = None
    tags: tuple[str, ...] = ()
    feeds: tuple[CommunityFeed, ...] = ("최신글",)


@dataclass(frozen=True)
class CommunityComment:
    id: str
    post_id: str
    author_name: str
    body: str
    created_at: str


@dataclass(frozen=True)
class CommunityReaction:
    id: str
    post_id: str
    reaction_type: CommunityReactionType
    created_at: str


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
class StructuredRecordBatch:
    candidates: tuple[StructuredRecordCandidate, ...]

    @property
    def needs_confirmation(self) -> bool:
        return any(candidate.needs_confirmation for candidate in self.candidates)


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
class ShoppingRecommendation:
    title: str
    product_url: str
    image_url: str
    mall_name: str
    lowest_price: int
    query: str
    reason: str
    source_record_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class VeterinaryHospitalRecommendation:
    place_id: str
    name: str
    address: str
    phone_number: str
    google_maps_url: str
    latitude: float | None
    longitude: float | None
    rating: float | None
    user_rating_count: int
    is_open_now: bool | None
    is_24_hours: bool
    weekday_text: tuple[str, ...]
    distance_meters: int | None
    reason: str


@dataclass(frozen=True)
class PlannedReminder:
    title: str
    due_date: str
    reason: str


@dataclass(frozen=True)
class CareSchedule:
    id: str
    pet_id: str
    category: str
    title: str
    due_date: str
    repeat_label: str
    note: str
    is_done: bool


@dataclass(frozen=True)
class SafetyNotice:
    level: InsightSeverity
    message: str


@dataclass(frozen=True)
class CareContext:
    pet: PetProfile
    recent_records: tuple[PetRecord, ...] = ()
    due_reminders: tuple[PlannedReminder, ...] = ()


@dataclass(frozen=True)
class CareKnowledgeSource:
    id: str
    url: str
    title: str
    allowed_domain: str
    enabled: bool = True


@dataclass(frozen=True)
class CareKnowledgeChunk:
    id: str
    source_id: str
    title: str
    text: str
    source_url: str
    content_hash: str


@dataclass(frozen=True)
class CareKnowledgeHit:
    chunk: CareKnowledgeChunk
    score: float

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from application.dto import PetLogAgentResult
from domain.enums import RecordInputSource
from domain.models import (
    CareSuggestion,
    PetRecord,
    PlannedReminder,
    SafetyNotice,
    ShoppingRecommendation,
    StructuredRecordCandidate,
)


class PetLogRecordRequest(BaseModel):
    pet_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source: RecordInputSource = "manual"
    confirm: bool = False

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be blank")
        return stripped


def success_response(data: dict[str, Any]) -> dict[str, Any]:
    return {"success": True, "data": data}


def pet_log_agent_result_to_dict(result: PetLogAgentResult) -> dict[str, Any]:
    return {
        "candidates": [_candidate_to_dict(candidate) for candidate in result.candidates],
        "saved_records": [_record_to_dict(record) for record in result.saved_records],
        "needs_confirmation": result.record_batch.needs_confirmation,
        "safety_notices": [_safety_notice_to_dict(notice) for notice in result.safety_notices],
        "suggestions": [_suggestion_to_dict(suggestion) for suggestion in result.suggestions],
        "shopping_recommendations": [
            _shopping_recommendation_to_dict(recommendation)
            for recommendation in result.shopping_recommendations
        ],
        "reminders": [_reminder_to_dict(reminder) for reminder in result.reminders],
    }


def _candidate_to_dict(candidate: StructuredRecordCandidate) -> dict[str, Any]:
    return {
        "title": candidate.title,
        "detail": candidate.detail,
        "category": candidate.category,
        "status": candidate.status,
        "confidence": candidate.confidence,
        "needs_confirmation": candidate.needs_confirmation,
        "measurements": list(candidate.measurements),
    }


def _record_to_dict(record: PetRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "pet_id": record.pet_id,
        "category": record.category,
        "title": record.title,
        "detail": record.detail,
        "status": record.status,
        "recorded_at": record.recorded_at,
        "source": record.source,
    }


def _safety_notice_to_dict(notice: SafetyNotice) -> dict[str, Any]:
    return {
        "level": notice.level,
        "message": notice.message,
    }


def _suggestion_to_dict(suggestion: CareSuggestion) -> dict[str, Any]:
    return {
        "title": suggestion.title,
        "action": suggestion.action,
        "reason": suggestion.reason,
        "source_record_ids": list(suggestion.source_record_ids),
    }


def _shopping_recommendation_to_dict(recommendation: ShoppingRecommendation) -> dict[str, Any]:
    return {
        "title": recommendation.title,
        "product_url": recommendation.product_url,
        "image_url": recommendation.image_url,
        "mall_name": recommendation.mall_name,
        "lowest_price": recommendation.lowest_price,
        "query": recommendation.query,
        "reason": recommendation.reason,
        "source_record_ids": list(recommendation.source_record_ids),
    }


def _reminder_to_dict(reminder: PlannedReminder) -> dict[str, Any]:
    return {
        "title": reminder.title,
        "due_date": reminder.due_date,
        "reason": reminder.reason,
    }

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from application.dto import PetLogAgentResult
from application.agents.hospital import HospitalRecommendationResult
from domain.enums import CommunityBoard, CommunityReactionType, RecordInputSource
from domain.models import (
    CareSuggestion,
    CommunityComment,
    CommunityPost,
    PetRecord,
    PlannedReminder,
    SafetyNotice,
    ShoppingRecommendation,
    StructuredRecordCandidate,
    VeterinaryHospitalRecommendation,
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


class HospitalRecommendationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_meters: float | None = Field(default=None, ge=0, le=100000)
    location_source: str = Field(default="gps", min_length=1, max_length=32)
    radius_meters: int = Field(default=3000, ge=100, le=50000)
    max_results: int = Field(default=5, ge=1, le=20)
    language_code: str = Field(default="ko", min_length=2, max_length=8)
    region_code: str = Field(default="KR", min_length=2, max_length=2)
    open_now_only: bool = True
    emergency: bool = False
    text: str = ""


class CommunityPostRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    board: CommunityBoard
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    author_name: str = Field(default="나", alias="authorName", min_length=1)
    distance: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("title", "body", "author_name")
    @classmethod
    def reject_blank_community_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank")
        return stripped

    @field_validator("distance")
    @classmethod
    def normalize_blank_distance(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        return [tag.strip() for tag in value if tag.strip()]


class CommunityCommentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    body: str = Field(min_length=1)
    author_name: str = Field(default="나", alias="authorName", min_length=1)

    @field_validator("body", "author_name")
    @classmethod
    def reject_blank_comment_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be blank")
        return stripped


class CommunityReactionRequest(BaseModel):
    reaction_type: CommunityReactionType = "like"


def success_response(data: dict[str, Any]) -> dict[str, Any]:
    return {"success": True, "data": data}


def hospital_recommendation_result_to_dict(
    result: HospitalRecommendationResult,
) -> dict[str, Any]:
    return {
        "current_time": result.current_time.isoformat(),
        "search_center": {
            "latitude": result.center_latitude,
            "longitude": result.center_longitude,
            "radius_meters": result.radius_meters,
            "location_source": result.location_source,
            "accuracy_meters": result.accuracy_meters,
            "emergency_mode": result.emergency_mode,
        },
        "recommendations": [
            _hospital_recommendation_to_dict(recommendation)
            for recommendation in result.recommendations
        ],
    }


def community_post_to_dict(post: CommunityPost) -> dict[str, Any]:
    return {
        "id": post.id,
        "board": post.board,
        "title": post.title,
        "body": post.body,
        "authorName": post.author_name,
        "createdAt": post.created_at,
        "comments": post.comments,
        "likes": post.likes,
        "distance": post.distance,
        "feeds": list(post.feeds),
        "tags": list(post.tags),
    }


def community_comment_to_dict(comment: CommunityComment) -> dict[str, Any]:
    return {
        "id": comment.id,
        "postId": comment.post_id,
        "authorName": comment.author_name,
        "body": comment.body,
        "createdAt": comment.created_at,
    }


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


def _hospital_recommendation_to_dict(recommendation: VeterinaryHospitalRecommendation) -> dict[str, Any]:
    return {
        "place_id": recommendation.place_id,
        "name": recommendation.name,
        "address": recommendation.address,
        "phone_number": recommendation.phone_number,
        "google_maps_url": recommendation.google_maps_url,
        "latitude": recommendation.latitude,
        "longitude": recommendation.longitude,
        "rating": recommendation.rating,
        "user_rating_count": recommendation.user_rating_count,
        "is_open_now": recommendation.is_open_now,
        "is_24_hours": recommendation.is_24_hours,
        "weekday_text": list(recommendation.weekday_text),
        "distance_meters": recommendation.distance_meters,
        "reason": recommendation.reason,
    }


def _reminder_to_dict(reminder: PlannedReminder) -> dict[str, Any]:
    return {
        "title": reminder.title,
        "due_date": reminder.due_date,
        "reason": reminder.reason,
    }

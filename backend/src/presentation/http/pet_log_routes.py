from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from application.dto import PetLogAgentInput, PetLogAgentResult
from composition import AppContext
from domain.models import CareSchedule, PetProfile, PetRecord
from presentation.http.schemas import (
    PetLogRecordRequest,
    pet_log_agent_result_to_dict,
    success_response,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
server_logger = logging.getLogger("uvicorn.error")


def build_pet_log_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/v1/pet-log/snapshot")
    def get_pet_log_snapshot(http_request: Request, pet_id: str) -> dict[str, object]:
        app_context = _app_context(http_request)
        try:
            pet = app_context.pet_profile_reader.get_pet(pet_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Pet not found") from exc

        if app_context.record_reader is None or app_context.schedule_reader is None:
            raise HTTPException(status_code=500, detail="Snapshot readers are not configured")

        records = app_context.record_reader.list_recent(pet_id, lookback_days=3650)
        schedules = app_context.schedule_reader.list_for_pet(pet_id)
        return success_response(_pet_log_snapshot_to_dict(pet, records, schedules))

    @router.post("/api/v1/pet-log/records")
    def handle_pet_log_record(http_request: Request, request: PetLogRecordRequest) -> dict[str, object]:
        app_context = _app_context(http_request)
        try:
            pet = app_context.pet_profile_reader.get_pet(request.pet_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Pet not found") from exc

        result = app_context.pet_log_agent_pipeline.handle(
            PetLogAgentInput(
                pet=pet,
                text=request.text,
                source=request.source,
                confirm=request.confirm,
            )
        )
        _log_pet_log_record_result(request, result)
        return success_response(pet_log_agent_result_to_dict(result))

    return router


def _app_context(request: Request) -> AppContext:
    return request.app.state.app_context


def _pet_log_snapshot_to_dict(
    pet: PetProfile,
    records: tuple[PetRecord, ...],
    schedules: tuple[CareSchedule, ...],
) -> dict[str, object]:
    return {
        "version": 1,
        "profile": {
            "name": pet.name,
            "breed": pet.breed or "",
            "age": pet.age_label or "",
            "sex": "",
            "weight": "",
            "birthday": "",
            "personality": pet.personality or "",
            "notes": list(pet.notes),
        },
        "records": [
            _record_to_frontend_entry(record)
            for record in sorted(records, key=lambda item: item.recorded_at, reverse=True)
        ],
        "schedules": [_schedule_to_frontend_entry(schedule) for schedule in schedules],
        "settings": {
            "notificationPreferences": {
                "missingRecord": True,
                "alert": True,
                "schedule": True,
            },
            "aiInsightEnabled": True,
        },
        "readNotificationIds": [],
        "expansionState": {
            "sharedCare": {},
            "hospital": {},
            "shopping": {},
        },
    }


def _record_to_frontend_entry(record: PetRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "date": _date_label(record.recorded_at),
        "time": _time_label(record.recorded_at),
        "category": record.category,
        "title": record.title,
        "detail": record.detail,
        "status": record.status,
    }


def _schedule_to_frontend_entry(schedule: CareSchedule) -> dict[str, object]:
    return {
        "id": schedule.id,
        "category": schedule.category,
        "title": schedule.title,
        "dueDate": schedule.due_date,
        "repeatLabel": schedule.repeat_label,
        "note": schedule.note,
        "isDone": schedule.is_done,
    }


def _date_label(value: str) -> str:
    date_part = value.split("T", maxsplit=1)[0]
    parts = date_part.split("-")
    if len(parts) != 3:
        return ""
    return f"{int(parts[1])}월 {int(parts[2])}일"


def _time_label(value: str) -> str:
    if "T" not in value:
        return ""
    time_part = value.split("T", maxsplit=1)[1].replace("Z", "")
    parts = time_part.split(":", maxsplit=2)
    if len(parts) < 2:
        return ""
    return f"{parts[0]}:{parts[1]}"


def _log_pet_log_record_result(request: PetLogRecordRequest, result: PetLogAgentResult) -> None:
    first_candidate = result.candidate
    first_saved_record = result.saved_record
    message = (
        'record.result | pet_id=%s | source=%s | mode=%s | confirm=%s | candidates=%d | saved=%d | '
        'needs_confirmation=%s | first="%s" | saved_id=%s'
    )
    args = (
        request.pet_id,
        request.source,
        _result_mode(request, result),
        _yes_no(request.confirm),
        len(result.candidates),
        len(result.saved_records),
        _yes_no(result.record_batch.needs_confirmation),
        f"{first_candidate.category}: {first_candidate.title}" if first_candidate else "-",
        first_saved_record.id if first_saved_record else "-",
    )
    logger.info(message, *args)
    server_logger.info(message, *args)


def _result_mode(request: PetLogRecordRequest, result: PetLogAgentResult) -> str:
    if request.source == "ai_preview":
        return "preview"
    if result.saved_records:
        return "saved"
    if result.record_batch.needs_confirmation and not request.confirm:
        return "pending_confirmation"
    return "processed"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"

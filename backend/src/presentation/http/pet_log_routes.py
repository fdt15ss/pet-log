from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from application.dto import PetLogAgentInput, PetLogAgentResult
from composition import AppContext
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

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from application.dto import PetLogAgentInput
from composition import AppContext
from presentation.http.schemas import (
    PetLogRecordRequest,
    pet_log_agent_result_to_dict,
    success_response,
)


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
        return success_response(pet_log_agent_result_to_dict(result))

    return router


def _app_context(request: Request) -> AppContext:
    return request.app.state.app_context

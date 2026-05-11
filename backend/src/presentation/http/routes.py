from __future__ import annotations

from fastapi import APIRouter

from presentation.http.file_routes import build_file_router
from presentation.http.pet_log_routes import build_pet_log_router
from presentation.http.speech_routes import build_speech_router


def build_router() -> APIRouter:
    router = APIRouter()
    router.include_router(build_pet_log_router())
    router.include_router(build_file_router())
    router.include_router(build_speech_router())

    @router.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return router

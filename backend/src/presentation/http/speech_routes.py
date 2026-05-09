from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from composition import AppContext
from presentation.http.schemas import success_response


MAX_AUDIO_UPLOAD_BYTES = 25 * 1024 * 1024


def build_speech_router() -> APIRouter:
    router = APIRouter()

    @router.post("/api/v1/speech/transcriptions")
    async def handle_speech_transcription(
        http_request: Request,
        audio: UploadFile = File(...),
    ) -> dict[str, object]:
        content_type = audio.content_type or ""
        if not content_type.split(";")[0].strip().lower().startswith("audio/"):
            raise HTTPException(status_code=415, detail="Unsupported audio content type")

        audio_bytes = await audio.read(MAX_AUDIO_UPLOAD_BYTES + 1)
        await audio.close()
        if not audio_bytes:
            raise HTTPException(status_code=422, detail="Audio file must not be empty")
        if len(audio_bytes) > MAX_AUDIO_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Audio file is too large")

        text = _app_context(http_request).speech_to_text.transcribe(audio_bytes, content_type)
        return success_response({"text": text})

    return router


def _app_context(request: Request) -> AppContext:
    return request.app.state.app_context

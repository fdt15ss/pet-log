from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from composition import AppContext
from presentation.http.schemas import success_response


MAX_AUDIO_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_TTS_TEXT_LENGTH = 500


class SpeechSynthesisRequest(BaseModel):
    text: str
    voice: str | None = None


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

    @router.post("/api/v1/speech/synthesis")
    async def handle_speech_synthesis(
        http_request: Request,
        synthesis_request: SpeechSynthesisRequest,
    ) -> Response:
        text = synthesis_request.text.strip()
        if not text:
            raise HTTPException(status_code=422, detail="Text must not be empty")
        if len(text) > MAX_TTS_TEXT_LENGTH:
            raise HTTPException(status_code=413, detail="Text is too long")

        context = _app_context(http_request)
        if context.text_to_speech is None:
            raise HTTPException(status_code=503, detail="Text-to-speech provider is not configured")

        try:
            audio = await run_in_threadpool(
                context.text_to_speech.synthesize,
                text,
                synthesis_request.voice,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Text-to-speech synthesis failed") from exc

        return Response(content=audio, media_type="audio/mpeg")

    return router


def _app_context(request: Request) -> AppContext:
    return request.app.state.app_context

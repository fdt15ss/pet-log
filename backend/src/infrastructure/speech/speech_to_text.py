from __future__ import annotations

from application.interfaces import SpeechToTextInterface


class SpeechToTextProvider(SpeechToTextInterface):
    def transcribe(self, audio: bytes, content_type: str) -> str:
        raise NotImplementedError

from __future__ import annotations

from application.interfaces import TextToSpeechInterface


class TextToSpeechProvider(TextToSpeechInterface):
    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        raise NotImplementedError

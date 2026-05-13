from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import Callable
from typing import Protocol

import edge_tts


DEFAULT_EDGE_TTS_VOICE = "ko-KR-SunHiNeural"


class EdgeCommunicate(Protocol):
    async def save(self, audio_path: str) -> None:
        raise NotImplementedError


EdgeCommunicateFactory = Callable[[str, str], EdgeCommunicate]


class TextToSpeechProvider:
    def __init__(
        self,
        *,
        default_voice: str | None = None,
        communicate_factory: EdgeCommunicateFactory | None = None,
    ) -> None:
        self._default_voice = default_voice or os.environ.get("EDGE_TTS_VOICE", DEFAULT_EDGE_TTS_VOICE)
        self._communicate_factory = communicate_factory or build_edge_communicate

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("text must not be empty.")

        selected_voice = voice or self._default_voice
        audio_path = ""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
            audio_path = audio_file.name

        try:
            communicator = self._communicate_factory(normalized_text, selected_voice)
            run_async(communicator.save(audio_path))
            with open(audio_path, "rb") as audio_file:
                audio = audio_file.read()
        finally:
            if audio_path:
                try:
                    os.unlink(audio_path)
                except FileNotFoundError:
                    pass

        if not audio:
            raise RuntimeError("Edge TTS did not produce audio.")
        return audio


def build_edge_communicate(text: str, voice: str) -> EdgeCommunicate:
    return edge_tts.Communicate(text, voice)


def run_async(coro: object) -> None:
    asyncio.run(coro)

from __future__ import annotations

import unittest
from pathlib import Path

from infrastructure.speech.speech_to_text import SpeechToTextProvider
from infrastructure.speech.text_to_speech import TextToSpeechProvider


class FakeWhisperModel:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[tuple[str, dict[str, object]]] = []

    def transcribe(self, audio_path: str, **options: object) -> dict[str, str]:
        self.calls.append((audio_path, options))
        self.seen_audio = Path(audio_path).read_bytes()
        return {"text": self.text}


class FakeEdgeCommunicate:
    calls: list[tuple[str, str]] = []

    def __init__(self, text: str, voice: str) -> None:
        self.text = text
        self.voice = voice
        self.calls.append((text, voice))

    async def save(self, audio_path: str) -> None:
        Path(audio_path).write_bytes(f"{self.voice}:{self.text}".encode("utf-8"))


class TestSpeechProviders(unittest.TestCase):
    def test_stt_uses_whisper_medium_by_default_and_transcribes_audio(self):
        created: list[dict[str, object]] = []
        model = FakeWhisperModel(" 산책 다녀왔어 ")

        def load_model(model_name: str, **kwargs: object) -> FakeWhisperModel:
            created.append({"model_name": model_name, "kwargs": kwargs})
            return model

        provider = SpeechToTextProvider(model_loader=load_model)

        result = provider.transcribe(b"audio-bytes", "audio/webm")

        self.assertEqual(result, "산책 다녀왔어")
        self.assertEqual(created, [{"model_name": "medium", "kwargs": {}}])
        self.assertEqual(model.seen_audio, b"audio-bytes")
        self.assertEqual(model.calls[0][1], {"fp16": False})

    def test_stt_can_override_model_and_transcribe_options(self):
        created: list[dict[str, object]] = []
        model = FakeWhisperModel("밥 먹었어")

        def load_model(model_name: str, **kwargs: object) -> FakeWhisperModel:
            created.append({"model_name": model_name, "kwargs": kwargs})
            return model

        provider = SpeechToTextProvider(
            model_name="small",
            model_loader=load_model,
            model_options={"device": "cpu"},
            transcribe_options={"language": "ko"},
        )

        result = provider.transcribe(b"audio", "audio/mpeg")

        self.assertEqual(result, "밥 먹었어")
        self.assertEqual(created, [{"model_name": "small", "kwargs": {"device": "cpu"}}])
        self.assertEqual(model.calls[0][1], {"fp16": False, "language": "ko"})

    def test_tts_uses_edge_tts_default_voice_and_returns_audio_bytes(self):
        FakeEdgeCommunicate.calls = []
        provider = TextToSpeechProvider(communicate_factory=FakeEdgeCommunicate)

        audio = provider.synthesize("안녕")

        self.assertEqual(audio, "ko-KR-SunHiNeural:안녕".encode("utf-8"))
        self.assertEqual(FakeEdgeCommunicate.calls, [("안녕", "ko-KR-SunHiNeural")])

    def test_tts_can_override_voice(self):
        FakeEdgeCommunicate.calls = []
        provider = TextToSpeechProvider(communicate_factory=FakeEdgeCommunicate)

        audio = provider.synthesize("초코야", voice="ko-KR-InJoonNeural")

        self.assertEqual(audio, "ko-KR-InJoonNeural:초코야".encode("utf-8"))
        self.assertEqual(FakeEdgeCommunicate.calls, [("초코야", "ko-KR-InJoonNeural")])


if __name__ == "__main__":
    unittest.main()

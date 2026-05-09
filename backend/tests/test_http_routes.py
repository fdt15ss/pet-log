import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from application.dto import PetLogAgentResult
from composition import AppContext
from domain.models import PetProfile, StructuredRecordCandidate
from presentation.http.app import create_app


class FakePetLogAgentPipeline:
    def __init__(self) -> None:
        self.handled_input = None

    def handle(self, input):
        self.handled_input = input
        return PetLogAgentResult(
            candidates=(
                StructuredRecordCandidate(
                    title="아침 식사",
                    detail="사료를 조금 남겼어요.",
                    category="meal",
                    status="notice",
                    confidence=0.82,
                    needs_confirmation=True,
                    measurements=("사료 조금 남김",),
                ),
            ),
        )


class FakePetProfileReader:
    def __init__(self) -> None:
        self.pets = {
            "sample-pet-choco": PetProfile(
                id="sample-pet-choco",
                name="초코",
                breed="말티푸",
                species="dog",
                age_label="3살",
                personality="저녁 산책을 좋아해요",
                notes=("아침 식사는 천천히 먹는 편",),
            )
        }

    def get_pet(self, pet_id: str) -> PetProfile:
        return self.pets[pet_id]


class FakeAppContext:
    def __init__(self) -> None:
        self.pet_log_agent_pipeline = FakePetLogAgentPipeline()
        self.pet_profile_reader = FakePetProfileReader()
        self.speech_to_text = FakeSpeechToText()
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeSpeechToText:
    def __init__(self) -> None:
        self.transcribed_audio = None
        self.transcribed_content_type = None

    def transcribe(self, audio: bytes, content_type: str) -> str:
        self.transcribed_audio = audio
        self.transcribed_content_type = content_type
        return "오늘 아침 사료를 조금 남겼어"


class TestHttpRoutes(unittest.TestCase):
    def test_create_app_loads_dotenv_without_explicit_path(self):
        with patch("presentation.http.app.load_dotenv") as load_dotenv:
            create_app(app_context_factory=FakeAppContext)

        load_dotenv.assert_called_once_with(override=False)

    def test_health_route_returns_ok(self):
        client = TestClient(create_app(app_context_factory=FakeAppContext))

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_record_route_converts_request_and_pipeline_result(self):
        context = FakeAppContext()

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.post(
                "/api/v1/pet-log/records",
                json={
                    "pet_id": "sample-pet-choco",
                    "text": "오늘 아침 사료를 조금 남겼어",
                    "source": "manual",
                    "confirm": False,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(context.pet_log_agent_pipeline.handled_input.pet.id, "sample-pet-choco")
        self.assertEqual(context.pet_log_agent_pipeline.handled_input.pet.name, "초코")
        self.assertEqual(context.pet_log_agent_pipeline.handled_input.text, "오늘 아침 사료를 조금 남겼어")
        self.assertEqual(context.pet_log_agent_pipeline.handled_input.source, "manual")
        self.assertFalse(context.pet_log_agent_pipeline.handled_input.confirm)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "data": {
                    "candidates": [
                        {
                            "title": "아침 식사",
                            "detail": "사료를 조금 남겼어요.",
                            "category": "meal",
                            "status": "notice",
                            "confidence": 0.82,
                            "needs_confirmation": True,
                            "measurements": ["사료 조금 남김"],
                        }
                    ],
                    "saved_records": [],
                    "needs_confirmation": True,
                    "safety_notices": [],
                    "suggestions": [],
                    "reminders": [],
                },
            },
        )

    def test_record_route_rejects_blank_text(self):
        client = TestClient(create_app(app_context_factory=FakeAppContext))

        response = client.post(
            "/api/v1/pet-log/records",
            json={
                "pet_id": "sample-pet-choco",
                "text": "   ",
                "source": "manual",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_record_route_returns_404_for_unknown_pet_id(self):
        with TestClient(create_app(app_context_factory=FakeAppContext)) as client:
            response = client.post(
                "/api/v1/pet-log/records",
                json={
                    "pet_id": "missing-pet",
                    "text": "오늘 아침 사료를 조금 남겼어",
                    "source": "manual",
                },
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Pet not found"})

    def test_pet_log_router_can_be_composed_independently(self):
        from fastapi import FastAPI

        from presentation.http.pet_log_routes import build_pet_log_router

        context = FakeAppContext()
        app = FastAPI()
        app.state.app_context = context
        app.include_router(build_pet_log_router())

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/pet-log/records",
                json={
                    "pet_id": "sample-pet-choco",
                    "text": "오늘 아침 사료를 조금 남겼어",
                    "source": "manual",
                    "confirm": False,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(context.pet_log_agent_pipeline.handled_input.pet.id, "sample-pet-choco")

    def test_lifespan_closes_app_context_on_shutdown(self):
        context = FakeAppContext()

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(context.closed)

    def test_create_app_accepts_prebuilt_context(self):
        context = AppContext(
            pet_log_agent_pipeline=FakePetLogAgentPipeline(),
            pet_profile_reader=FakePetProfileReader(),
            speech_to_text=FakeSpeechToText(),
        )

        with TestClient(create_app(app_context=context)) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)

    def test_speech_transcription_route_accepts_audio_file(self):
        context = FakeAppContext()

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.post(
                "/api/v1/speech/transcriptions",
                files={"audio": ("recording.webm", b"audio-bytes", "audio/webm")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(context.speech_to_text.transcribed_audio, b"audio-bytes")
        self.assertEqual(context.speech_to_text.transcribed_content_type, "audio/webm")
        self.assertEqual(
            response.json(),
            {"success": True, "data": {"text": "오늘 아침 사료를 조금 남겼어"}},
        )

    def test_speech_router_can_be_composed_independently(self):
        from fastapi import FastAPI

        from presentation.http.speech_routes import build_speech_router

        context = FakeAppContext()
        app = FastAPI()
        app.state.app_context = context
        app.include_router(build_speech_router())

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/speech/transcriptions",
                files={"audio": ("recording.webm", b"audio-bytes", "audio/webm")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(context.speech_to_text.transcribed_audio, b"audio-bytes")

    def test_speech_transcription_route_rejects_empty_audio_file(self):
        with TestClient(create_app(app_context_factory=FakeAppContext)) as client:
            response = client.post(
                "/api/v1/speech/transcriptions",
                files={"audio": ("empty.webm", b"", "audio/webm")},
            )

        self.assertEqual(response.status_code, 422)

    def test_speech_transcription_route_rejects_non_audio_content_type(self):
        with TestClient(create_app(app_context_factory=FakeAppContext)) as client:
            response = client.post(
                "/api/v1/speech/transcriptions",
                files={"audio": ("notes.txt", b"not audio", "text/plain")},
            )

        self.assertEqual(response.status_code, 415)


if __name__ == "__main__":
    unittest.main()

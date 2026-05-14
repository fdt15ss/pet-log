import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from application.dto import CareQuestionResult, PetChatResult
from presentation.http.app import create_app
from domain.models import SafetyNotice, CareSuggestion, InsightSeverity, PetProfile

class FakeAppContext:
    def __init__(self):
        self.risk_detection_agent = MagicMock()
        self.context_analysis_agent = MagicMock()
        self.suggestion_agent = MagicMock()
        self.record_reader = MagicMock()
        self.schedule_reader = MagicMock()
        self.pet_profile_reader = MagicMock()
        self.pet_log_agent_pipeline = MagicMock()
        self.speech_to_text = MagicMock()
        self.care_question_pipeline = None
        self.pet_chat_pipeline = None
        self.hospital_recommendation_agent = MagicMock()
        self.closed = False

    def close(self):
        self.closed = True

class TestAIEndpoints(unittest.TestCase):
    def test_get_insights_returns_safety_notices(self):
        context = FakeAppContext()
        context.record_reader.list_recent.return_value = []
        context.risk_detection_agent.detect.return_value = [
            SafetyNotice(level="alert", message="Danger!")
        ]
        
        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.get("/api/v1/ai/insights?pet_id=pet-1")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("insights", data)
        self.assertEqual(data["insights"][0]["message"], "Danger!")
        context.record_reader.list_recent.assert_called_once_with("pet-1", lookback_days=30)
        context.risk_detection_agent.detect.assert_called_once()

    def test_get_suggestions_returns_care_suggestions(self):
        context = FakeAppContext()
        context.record_reader.list_recent.return_value = []
        context.schedule_reader.list_due_items.return_value = []
        context.pet_profile_reader.get_pet.return_value = PetProfile(id="pet-1", name="초코")
        context.context_analysis_agent.analyze.return_value = MagicMock()
        context.suggestion_agent.suggest.return_value = [
            CareSuggestion(title="Play", action="Go play", reason="Fun")
        ]
        
        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.get("/api/v1/ai/suggestions?pet_id=pet-1")
            
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertIn("suggestions", data)
        self.assertEqual(data["suggestions"][0]["title"], "Play")
        context.record_reader.list_recent.assert_called_once_with("pet-1", lookback_days=30)
        context.schedule_reader.list_due_items.assert_called_once_with("pet-1", days_ahead=14)
        context.suggestion_agent.suggest.assert_called_once()

    def test_post_care_answer_returns_pipeline_answer(self):
        context = FakeAppContext()
        context.pet_profile_reader.get_pet.return_value = PetProfile(id="pet-1", name="초코")
        context.care_question_pipeline = MagicMock()
        context.care_question_pipeline.ask.return_value = CareQuestionResult(
            answer="오늘 기록 기준으로는 물 섭취와 컨디션을 같이 봐주세요.",
            referenced_record_ids=("record-1",),
        )

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.post(
                "/api/v1/ai/care-answer",
                json={"pet_id": "pet-1", "question": "오늘 컨디션 어때?"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["answer"], "오늘 기록 기준으로는 물 섭취와 컨디션을 같이 봐주세요.")
        self.assertEqual(data["referencedRecordIds"], ["record-1"])
        context.pet_profile_reader.get_pet.assert_called_once_with("pet-1")
        context.care_question_pipeline.ask.assert_called_once_with("pet-1", "오늘 컨디션 어때?")

    def test_post_pet_chat_returns_pipeline_answer(self):
        context = FakeAppContext()
        context.pet_profile_reader.get_pet.return_value = PetProfile(id="pet-1", name="초코")
        context.pet_chat_pipeline = MagicMock()
        context.pet_chat_pipeline.chat.return_value = PetChatResult(answer="나 오늘 산책해서 기분 좋아!")

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.post(
                "/api/v1/ai/pet-chat",
                json={"pet_id": "pet-1", "message": "오늘 기분 어때?"},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["answer"], "나 오늘 산책해서 기분 좋아!")
        self.assertFalse(data["routedToCareQuestion"])
        context.pet_profile_reader.get_pet.assert_called_once_with("pet-1")
        context.pet_chat_pipeline.chat.assert_called_once_with("pet-1", "오늘 기분 어때?")

if __name__ == "__main__":
    unittest.main()

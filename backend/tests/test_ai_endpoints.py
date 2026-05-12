import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
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

if __name__ == "__main__":
    unittest.main()

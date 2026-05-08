from __future__ import annotations

import unittest

from application.dto import NotificationCandidate, ProactiveQuestionResult
from application.interfaces import (
    ImageRecordUnderstandingProviderInterface,
    NotificationPolicyInterface,
    ProactiveQuestionPolicyInterface,
)
from domain.models import ContextAnalysisResult, PetProfile, PlannedReminder, SafetyNotice, StructuredRecordCandidate
from infrastructure.agents.notification_agent import NotificationAgent
from infrastructure.agents.photo_record_understanding_agent import PhotoRecordUnderstandingAgent
from infrastructure.agents.proactive_question_agent import ProactiveQuestionAgent


class FakeProactiveQuestionPolicy(ProactiveQuestionPolicyInterface):
    def build_question(
        self,
        pet: PetProfile,
        records: tuple[object, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> ProactiveQuestionResult | None:
        raise AssertionError("skeleton should not call policy yet")


class FakeNotificationPolicy(NotificationPolicyInterface):
    def plan(
        self,
        pet: PetProfile,
        context: ContextAnalysisResult,
        safety_notices: tuple[SafetyNotice, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[NotificationCandidate, ...]:
        raise AssertionError("skeleton should not call policy yet")


class FakeImageRecordUnderstandingProvider(ImageRecordUnderstandingProviderInterface):
    def understand(
        self,
        pet: PetProfile,
        image: bytes,
        content_type: str,
        user_note: str | None = None,
    ) -> StructuredRecordCandidate:
        raise AssertionError("skeleton should not call provider yet")


class TestAgentSkeletons(unittest.TestCase):
    def test_proactive_question_agent_accepts_policy_but_has_no_behavior_yet(self):
        agent = ProactiveQuestionAgent(FakeProactiveQuestionPolicy())

        with self.assertRaises(NotImplementedError):
            agent.build_question(PetProfile(id="pet-1", name="초코"), (), ContextAnalysisResult(), ())

    def test_notification_agent_accepts_policy_but_has_no_behavior_yet(self):
        agent = NotificationAgent(FakeNotificationPolicy())

        with self.assertRaises(NotImplementedError):
            agent.plan(PetProfile(id="pet-1", name="초코"), ContextAnalysisResult(), (), ())

    def test_photo_record_understanding_agent_accepts_provider_but_has_no_behavior_yet(self):
        agent = PhotoRecordUnderstandingAgent(FakeImageRecordUnderstandingProvider())

        with self.assertRaises(NotImplementedError):
            agent.understand(PetProfile(id="pet-1", name="초코"), b"image", "image/png")


if __name__ == "__main__":
    unittest.main()

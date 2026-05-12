"""Tests for NotificationPolicy - RED phase (should fail before implementation)."""
from __future__ import annotations

import unittest

from application.dto import NotificationCandidate
from domain.models import CareInsight, ContextAnalysisResult, PetProfile, PlannedReminder, SafetyNotice
from infrastructure.notifications.policy import NotificationPolicy


class TestNotificationPolicy(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = NotificationPolicy()
        self.pet = PetProfile(id="pet-1", name="초코")
        self.empty_context = ContextAnalysisResult()

    def test_returns_empty_when_all_inputs_empty(self) -> None:
        result = self.policy.plan(self.pet, self.empty_context, (), ())

        self.assertEqual(result, ())

    def test_generates_missing_record_candidate_from_missing_record_insight(self) -> None:
        context = ContextAnalysisResult(
            missing_record_insights=(
                CareInsight(
                    severity="notice",
                    title="최근 기록 없음",
                    reason="초코의 최근 케어 기록이 없어 식사 흐름을 판단하기 어렵습니다.",
                ),
            ),
        )

        result = self.policy.plan(self.pet, context, (), ())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind, "missing_record")
        self.assertIsInstance(result[0].dedupe_key, str)
        self.assertTrue(len(result[0].dedupe_key) > 0)

    def test_generates_risk_candidate_from_alert_insight(self) -> None:
        context = ContextAnalysisResult(
            insights=(
                CareInsight(
                    severity="alert",
                    title="반복 주의 신호",
                    reason="이틀 연속 경계 반응이 나타났습니다.",
                    source_record_ids=("record-1", "record-2"),
                ),
            ),
        )

        result = self.policy.plan(self.pet, context, (), ())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind, "risk")
        self.assertEqual(result[0].source_record_ids, ("record-1", "record-2"))

    def test_generates_behavior_change_candidate_from_notice_insight(self) -> None:
        context = ContextAnalysisResult(
            insights=(
                CareInsight(
                    severity="notice",
                    title="식사 변화 감지",
                    reason="최근 식사량이 줄었습니다.",
                ),
            ),
        )

        result = self.policy.plan(self.pet, context, (), ())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind, "behavior_change")

    def test_generates_risk_candidate_with_safety_notice_attached(self) -> None:
        safety_notices = (SafetyNotice(level="alert", message="병원 방문을 권장합니다."),)

        result = self.policy.plan(self.pet, self.empty_context, safety_notices, ())

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind, "risk")
        self.assertEqual(result[0].safety_notice, safety_notices[0])

    def test_generates_schedule_candidate_from_due_item(self) -> None:
        due_items = (PlannedReminder(title="백신 접종", due_date="2026-05-15", reason="연간 예방접종 시기입니다."),)

        result = self.policy.plan(self.pet, self.empty_context, (), due_items)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].kind, "schedule")
        self.assertEqual(result[0].due_date, "2026-05-15")

    def test_generates_multiple_candidates_from_mixed_inputs(self) -> None:
        context = ContextAnalysisResult(
            insights=(CareInsight(severity="alert", title="위험 신호", reason="증상이 반복됩니다."),),
            missing_record_insights=(CareInsight(severity="notice", title="기록 누락", reason="기록이 없습니다."),),
        )
        due_items = (PlannedReminder(title="심장사상충 예방", due_date="2026-05-20", reason="월간 예방"),)

        result = self.policy.plan(self.pet, context, (), due_items)

        self.assertEqual(len(result), 3)
        kinds = {c.kind for c in result}
        self.assertIn("risk", kinds)
        self.assertIn("missing_record", kinds)
        self.assertIn("schedule", kinds)

    def test_each_candidate_has_unique_dedupe_key(self) -> None:
        context = ContextAnalysisResult(
            insights=(
                CareInsight(severity="alert", title="위험 A", reason="이유 A"),
                CareInsight(severity="notice", title="변화 B", reason="이유 B"),
            ),
        )

        result = self.policy.plan(self.pet, context, (), ())

        dedupe_keys = [c.dedupe_key for c in result]
        self.assertEqual(len(dedupe_keys), len(set(dedupe_keys)))

    def test_candidate_title_is_non_empty(self) -> None:
        context = ContextAnalysisResult(
            missing_record_insights=(CareInsight(severity="notice", title="기록 없음", reason="이유"),),
        )

        result = self.policy.plan(self.pet, context, (), ())

        for candidate in result:
            self.assertTrue(len(candidate.title) > 0)

    def test_candidate_message_is_non_empty(self) -> None:
        due_items = (PlannedReminder(title="예방접종", due_date="2026-06-01", reason="연간 접종"),)

        result = self.policy.plan(self.pet, self.empty_context, (), due_items)

        for candidate in result:
            self.assertTrue(len(candidate.message) > 0)


if __name__ == "__main__":
    unittest.main()

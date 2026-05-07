from __future__ import annotations

import json
import unittest

from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder
from infrastructure.llm.record_summary_provider import RecordSummaryProvider


class FakeOpenAITransport:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str], dict[str, object], float]] = []

    def __call__(
        self,
        endpoint: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout: float,
    ) -> dict[str, object]:
        self.calls.append((endpoint, headers, payload, timeout))
        return self.response


class TestRecordSummaryProvider(unittest.TestCase):
    def test_summarize_calls_openai_responses_api_and_parses_structured_output(self):
        model_output = {
            "summary": "초코의 새벽 짖음 기록이 반복되는지 지켜볼 필요가 있습니다.",
            "record_ids": ["record-1"],
            "highlights": ["새벽 짖음"],
            "behavior_patterns": ["현관 쪽 반응"],
            "missing_record_notes": ["짖음 이후 안정 여부 기록이 있으면 좋습니다."],
            "safety_notice": None,
        }
        transport = FakeOpenAITransport(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(model_output, ensure_ascii=False),
                            }
                        ],
                    }
                ]
            }
        )
        provider = RecordSummaryProvider(api_key="test-key", model="test-model", transport=transport)
        pet = PetProfile(id="pet-1", name="초코")
        records = (
            PetRecord(
                id="record-1",
                pet_id="pet-1",
                category="behavior",
                title="밤에 짖음",
                detail="새벽에 현관 쪽을 보고 10분 정도 짖었다.",
                status="notice",
                recorded_at="2026-05-07T01:10:00+09:00",
                source="manual",
            ),
        )
        due_items = (PlannedReminder(title="산책", due_date="2026-05-07", reason="저녁 산책 예정"),)

        result = provider.summarize(pet, records, ContextAnalysisResult(), due_items)

        self.assertEqual(result.summary, model_output["summary"])
        self.assertEqual(result.record_ids, ("record-1",))
        self.assertEqual(result.highlights, ("새벽 짖음",))
        self.assertEqual(len(transport.calls), 1)

        endpoint, headers, payload, timeout = transport.calls[0]
        self.assertEqual(endpoint, "https://api.openai.com/v1/responses")
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(timeout, 30.0)
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertEqual(payload["text"]["format"]["name"], "record_summary_result")
        self.assertIn("진단을 단정하지 마세요", payload["instructions"])
        self.assertIn("밤에 짖음", json.dumps(payload["input"], ensure_ascii=False))

    def test_summarize_requires_api_key(self):
        provider = RecordSummaryProvider(api_key="")

        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            provider.summarize(PetProfile(id="pet-1", name="초코"), (), ContextAnalysisResult(), ())


if __name__ == "__main__":
    unittest.main()

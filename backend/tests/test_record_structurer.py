from __future__ import annotations

import unittest

from application.dto import PetLogAgentInput
from domain.models import PetProfile
from infrastructure.llm.record_structuring import RecordStructurer


class FakeStructuredModel:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls: list[list[tuple[str, str]]] = []

    def invoke(self, messages: list[tuple[str, str]]) -> dict[str, object]:
        self.calls.append(messages)
        return self.response


class TestRecordStructurer(unittest.TestCase):
    def test_structure_invokes_model_and_maps_batch(self):
        model_output = {
            "candidates": [
                {
                    "title": "식사",
                    "detail": "오전 8시에 사료 40g 중 15g만 먹음",
                    "category": "meal",
                    "status": "notice",
                    "confidence": 0.92,
                    "needs_confirmation": False,
                    "measurements": ["오전 8시", "사료 40g", "섭취 15g"],
                },
                {
                    "title": "산책",
                    "detail": "저녁 산책을 12분만 함",
                    "category": "walk",
                    "status": "notice",
                    "confidence": 0.9,
                    "needs_confirmation": False,
                    "measurements": ["12분"],
                },
                {
                    "title": "귀 긁음",
                    "detail": "오른쪽 귀를 5번 긁음",
                    "category": "medical",
                    "status": "notice",
                    "confidence": 0.82,
                    "needs_confirmation": True,
                    "measurements": ["오른쪽 귀", "5번"],
                },
            ],
        }
        structured_model = FakeStructuredModel(model_output)
        structurer = RecordStructurer(
            api_key="test-key",
            model="test-model",
            structured_model=structured_model,
        )
        input = PetLogAgentInput(
            pet=PetProfile(id="pet-1", name="초코", species="companion"),
            text="오늘 오전 8시에 초코가 사료 40g 중 15g만 먹고, 저녁 산책은 12분만 했고, 오른쪽 귀를 5번 긁었어.",
            source="manual",
        )

        batch = structurer.structure(input)

        self.assertEqual(len(batch.candidates), 3)
        self.assertEqual(tuple(candidate.category for candidate in batch.candidates), ("meal", "walk", "medical"))
        self.assertEqual(tuple(candidate.title for candidate in batch.candidates), ("식사", "산책", "귀 긁음"))
        self.assertEqual(
            tuple(candidate.measurements for candidate in batch.candidates),
            (("오전 8시", "사료 40g", "섭취 15g"), ("12분",), ("오른쪽 귀", "5번")),
        )
        self.assertEqual(tuple(candidate.needs_confirmation for candidate in batch.candidates), (False, False, True))
        self.assertTrue(batch.needs_confirmation)
        self.assertEqual(len(structured_model.calls), 1)

        messages = structured_model.calls[0]
        self.assertEqual(messages[0][0], "system")
        self.assertEqual(messages[1][0], "user")
        self.assertIn("여러 사건이 섞이면 후보를 나누세요", messages[0][1])
        self.assertIn("사료 40g 중 15g", messages[1][1])
        self.assertIn("meal", messages[1][1])
        self.assertIn("walk", messages[1][1])
        self.assertIn("medical", messages[1][1])

    def test_builds_structured_model_with_configured_model(self):
        created: list[dict[str, object]] = []
        structured_model = FakeStructuredModel({"candidates": []})

        def fake_model_factory(model: str, api_key: str, timeout: float):
            created.append({"model": model, "api_key": api_key, "timeout": timeout})
            return structured_model

        structurer = RecordStructurer(
            api_key="test-key",
            model="test-model",
            timeout=12.0,
            model_factory=fake_model_factory,
        )

        structurer.structure(
            PetLogAgentInput(
                pet=PetProfile(id="pet-1", name="초코"),
                text="오늘 밥을 먹었어",
                source="manual",
            )
        )

        self.assertEqual(created, [{"model": "test-model", "api_key": "test-key", "timeout": 12.0}])

    def test_structure_requires_api_key(self):
        structurer = RecordStructurer(api_key="")

        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            structurer.structure(
                PetLogAgentInput(
                    pet=PetProfile(id="pet-1", name="초코"),
                    text="오늘 밥을 먹었어",
                    source="manual",
                )
            )


if __name__ == "__main__":
    unittest.main()

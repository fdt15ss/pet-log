from __future__ import annotations

import unittest
from unittest.mock import patch

from domain.models import ContextAnalysisResult, PetProfile
from infrastructure.llm.model_factory import build_chat_openai_model
from infrastructure.llm.record_summary import RecordSummaryProvider


class FakeChatOpenAI:
    calls: list[dict[str, object]] = []

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        FakeChatOpenAI.calls.append(kwargs)


class FakeFallbackCapableModel:
    def __init__(self, response: dict[str, object], error: BaseException | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[list[tuple[str, str]]] = []
        self.fallbacks: tuple[FakeFallbackModel, ...] = ()
        self.exceptions_to_handle: tuple[type[BaseException], ...] = ()

    def invoke(self, messages: list[tuple[str, str]]) -> dict[str, object]:
        self.calls.append(messages)
        if self.error is not None:
            raise self.error
        return self.response

    def with_fallbacks(
        self,
        fallbacks: list[FakeFallbackModel],
        *,
        exceptions_to_handle: tuple[type[BaseException], ...],
    ) -> FakeFallbackModel:
        self.fallbacks = tuple(fallbacks)
        self.exceptions_to_handle = exceptions_to_handle
        return FakeFallbackModel(self, self.fallbacks, exceptions_to_handle)


class FakeFallbackModel:
    def __init__(
        self,
        primary: FakeFallbackCapableModel | None,
        fallbacks: tuple[FakeFallbackModel, ...],
        exceptions_to_handle: tuple[type[BaseException], ...],
        response: dict[str, object] | None = None,
    ) -> None:
        self.primary = primary
        self.fallbacks = fallbacks
        self.exceptions_to_handle = exceptions_to_handle
        self.response = response or {}
        self.calls: list[list[tuple[str, str]]] = []

    def invoke(self, messages: list[tuple[str, str]]) -> dict[str, object]:
        self.calls.append(messages)
        if self.primary is None:
            return self.response

        try:
            return self.primary.invoke(messages)
        except self.exceptions_to_handle:
            return self.fallbacks[0].invoke(messages)


class TestLocalGemmaFallback(unittest.TestCase):
    def setUp(self) -> None:
        FakeChatOpenAI.calls = []

    def test_chat_model_builder_uses_local_gemma_endpoint(self):
        env = {
            "GEMMA_BASE_URL": "http://127.0.0.1:1234/v1",
            "GEMMA_MODEL": "google/gemma-3n-E4B-it",
        }

        with patch.dict("os.environ", env, clear=True), patch(
            "infrastructure.llm.model_factory.ChatOpenAI",
            FakeChatOpenAI,
        ):
            model = build_chat_openai_model("google/gemma-3n-E4B-it", "local-key", 9.0)

        self.assertIsInstance(model, FakeChatOpenAI)
        self.assertEqual(
            FakeChatOpenAI.calls,
            [
                {
                    "model": "gemma3n:e4b",
                    "api_key": "local-key",
                    "timeout": 9.0,
                    "base_url": "http://127.0.0.1:1234/v1",
                    "use_responses_api": False,
                }
            ],
        )

    def test_chat_model_builder_keeps_gpt_on_openai_responses_api(self):
        with patch.dict("os.environ", {}, clear=True), patch(
            "infrastructure.llm.model_factory.ChatOpenAI",
            FakeChatOpenAI,
        ):
            model = build_chat_openai_model("gpt-5-mini", "openai-key", 8.0)

        self.assertIsInstance(model, FakeChatOpenAI)
        self.assertEqual(
            FakeChatOpenAI.calls,
            [
                {
                    "model": "gpt-5-mini",
                    "api_key": "openai-key",
                    "timeout": 8.0,
                    "use_responses_api": True,
                }
            ],
        )

    def test_record_summary_uses_local_gemma_primary_and_gpt_fallback(self):
        created: list[dict[str, object]] = []
        primary_model = FakeFallbackCapableModel(
            {
                "summary": "",
                "record_ids": [],
                "highlights": [],
                "behavior_patterns": [],
                "missing_record_notes": [],
                "safety_notice": None,
            },
            error=TimeoutError("local model timed out"),
        )
        fallback_model = FakeFallbackModel(
            None,
            (),
            (),
            response={
                "summary": "GPT fallback 요약입니다.",
                "record_ids": [],
                "highlights": [],
                "behavior_patterns": [],
                "missing_record_notes": [],
                "safety_notice": None,
            },
        )

        def fake_model_factory(model: str, api_key: str, timeout: float):
            created.append({"model": model, "api_key": api_key, "timeout": timeout})
            if model == "gemma3n:e4b":
                return primary_model
            if model == "gpt-5-mini":
                return fallback_model
            raise AssertionError(f"Unexpected model: {model}")

        env = {
            "GEMMA_BASE_URL": "http://127.0.0.1:1234/v1",
            "GEMMA_MODEL": "google/gemma-3n-E4B-it",
            "GEMMA_API_KEY": "local-key",
            "OPENAI_API_KEY": "gpt-key",
            "OPENAI_RECORD_SUMMARY_MODEL": "gpt-5-mini",
        }
        with patch.dict("os.environ", env, clear=True):
            provider = RecordSummaryProvider(timeout=11.0, model_factory=fake_model_factory)
            result = provider.summarize(PetProfile(id="pet-1", name="초코"), (), ContextAnalysisResult(), ())

        self.assertEqual(result.summary, "GPT fallback 요약입니다.")
        self.assertEqual(
            created,
            [
                {"model": "gemma3n:e4b", "api_key": "local-key", "timeout": 11.0},
                {"model": "gpt-5-mini", "api_key": "gpt-key", "timeout": 11.0},
            ],
        )
        self.assertEqual(len(primary_model.calls), 1)
        self.assertEqual(len(fallback_model.calls), 1)
        self.assertIn(TimeoutError, primary_model.exceptions_to_handle)

    def test_provider_eager_load_builds_model_during_initialization(self):
        created: list[dict[str, object]] = []
        structured_model = FakeFallbackCapableModel(
            {
                "summary": "요약",
                "record_ids": [],
                "highlights": [],
                "behavior_patterns": [],
                "missing_record_notes": [],
                "safety_notice": None,
            }
        )

        def fake_model_factory(model: str, api_key: str, timeout: float):
            created.append({"model": model, "api_key": api_key, "timeout": timeout})
            return structured_model

        with patch.dict("os.environ", {"LLM_EAGER_LOAD": "1"}, clear=True):
            RecordSummaryProvider(
                api_key="test-key",
                model="test-model",
                timeout=3.0,
                model_factory=fake_model_factory,
            )

        self.assertEqual(created, [{"model": "test-model", "api_key": "test-key", "timeout": 3.0}])


if __name__ == "__main__":
    unittest.main()

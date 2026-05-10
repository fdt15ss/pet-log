from __future__ import annotations

import unittest
from unittest.mock import patch

from infrastructure.llm.local_runtime import (
    ensure_local_gemma_runtime,
    local_gemma_base_url,
    should_autopull_local_gemma_model,
    should_autostart_local_gemma,
    should_preload_local_gemma_model,
)
from infrastructure.llm.model_factory import build_chat_openai_model


class FakeChatOpenAI:
    calls: list[dict[str, object]] = []

    def __init__(self, **kwargs: object) -> None:
        FakeChatOpenAI.calls.append(kwargs)


class TestLLMLocalRuntime(unittest.TestCase):
    def setUp(self) -> None:
        FakeChatOpenAI.calls = []

    def test_vllm_autostart_uses_default_openai_compatible_base_url(self):
        with patch.dict("os.environ", {"LOCAL_LLM_AUTOSTART": "1"}, clear=True):
            self.assertTrue(should_autostart_local_gemma())
            self.assertEqual(local_gemma_base_url(), "http://127.0.0.1:8000/v1")

    def test_llama_cpp_runtime_uses_default_openai_compatible_base_url(self):
        env = {
            "LOCAL_LLM_AUTOSTART": "1",
            "LOCAL_LLM_RUNTIME": "llama_cpp",
        }
        with patch.dict("os.environ", env, clear=True):
            self.assertTrue(should_autostart_local_gemma())
            self.assertEqual(local_gemma_base_url(), "http://127.0.0.1:8080/v1")

    def test_model_builder_prepares_local_runtime_before_gemma_model_creation(self):
        prepared: list[str] = []
        env = {
            "LOCAL_LLM_AUTOSTART": "1",
            "GEMMA_MODEL": "google/gemma-3n-E4B-it",
        }

        with patch.dict("os.environ", env, clear=True), patch(
            "infrastructure.llm.model_factory.ChatOpenAI",
            FakeChatOpenAI,
        ), patch(
            "infrastructure.llm.model_factory.ensure_local_gemma_runtime",
            lambda: prepared.append("prepared"),
        ):
            build_chat_openai_model("google/gemma-3n-E4B-it", "local-gemma", 5.0)

        self.assertEqual(prepared, ["prepared"])
        self.assertEqual(
            FakeChatOpenAI.calls,
            [
                {
                    "model": "google/gemma-3n-E4B-it",
                    "api_key": "local-gemma",
                    "timeout": 5.0,
                    "base_url": "http://127.0.0.1:8000/v1",
                    "use_responses_api": False,
                }
            ],
        )

    def test_auto_pull_is_opt_in(self):
        with patch.dict("os.environ", {"LOCAL_LLM_AUTOSTART": "1"}, clear=True):
            self.assertFalse(should_autopull_local_gemma_model())

        with patch.dict("os.environ", {"LOCAL_LLM_AUTOSTART": "1", "GEMMA_AUTO_PULL": "1"}, clear=True):
            self.assertTrue(should_autopull_local_gemma_model())

    def test_preload_is_opt_in(self):
        with patch.dict("os.environ", {"LOCAL_LLM_AUTOSTART": "1"}, clear=True):
            self.assertFalse(should_preload_local_gemma_model())

        with patch.dict("os.environ", {"LOCAL_LLM_AUTOSTART": "1", "GEMMA_PRELOAD": "1"}, clear=True):
            self.assertTrue(should_preload_local_gemma_model())

    def test_ensure_vllm_runtime_downloads_starts_and_warms_model_when_enabled(self):
        commands: list[list[str]] = []
        run_commands: list[list[str]] = []
        warmed_urls: list[str] = []

        class FakeProcess:
            def poll(self):
                return None

        def fake_popen(command, **kwargs):
            commands.append(command)
            return FakeProcess()

        def fake_run(command, **kwargs):
            run_commands.append(command)

        env = {
            "LOCAL_LLM_AUTOSTART": "1",
            "LOCAL_LLM_RUNTIME": "vllm",
            "GEMMA_AUTO_PULL": "1",
            "GEMMA_PRELOAD": "1",
            "GEMMA_MODEL": "google/gemma-3n-E4B-it",
        }
        with patch.dict("os.environ", env, clear=True), patch(
            "infrastructure.llm.local_runtime._is_openai_compatible_server_ready",
            side_effect=[False, True],
        ), patch(
            "infrastructure.llm.local_runtime.subprocess.run",
            fake_run,
        ), patch(
            "infrastructure.llm.local_runtime.subprocess.Popen",
            fake_popen,
        ), patch(
            "infrastructure.llm.local_runtime._post_chat_completion",
            lambda base_url: warmed_urls.append(base_url),
        ):
            ensure_local_gemma_runtime()

        self.assertEqual(
            run_commands,
            [
                ["huggingface-cli", "download", "google/gemma-3n-E4B-it"],
            ],
        )
        self.assertEqual(commands, [["vllm", "serve", "google/gemma-3n-E4B-it", "--host", "127.0.0.1", "--port", "8000"]])
        self.assertEqual(warmed_urls, ["http://127.0.0.1:8000/v1"])

    def test_ensure_llama_cpp_runtime_downloads_starts_and_warms_model_when_enabled(self):
        commands: list[list[str]] = []
        run_commands: list[list[str]] = []
        warmed_urls: list[str] = []

        class FakeProcess:
            def poll(self):
                return None

        def fake_popen(command, **kwargs):
            commands.append(command)
            return FakeProcess()

        def fake_run(command, **kwargs):
            run_commands.append(command)

        env = {
            "LOCAL_LLM_AUTOSTART": "1",
            "LOCAL_LLM_RUNTIME": "llama_cpp",
            "GEMMA_AUTO_PULL": "1",
            "GEMMA_PRELOAD": "1",
            "GEMMA_MODEL": "google/gemma-3n-E4B-it",
        }
        with patch.dict("os.environ", env, clear=True), patch(
            "infrastructure.llm.local_runtime._is_openai_compatible_server_ready",
            side_effect=[False, True],
        ), patch(
            "infrastructure.llm.local_runtime.subprocess.run",
            fake_run,
        ), patch(
            "infrastructure.llm.local_runtime.subprocess.Popen",
            fake_popen,
        ), patch(
            "infrastructure.llm.local_runtime._post_chat_completion",
            lambda base_url: warmed_urls.append(base_url),
        ):
            ensure_local_gemma_runtime()

        self.assertEqual(
            run_commands,
            [
                [
                    "huggingface-cli",
                    "download",
                    "ggml-org/gemma-3n-E4B-it-GGUF",
                    "gemma-3n-E4B-it-Q8_0.gguf",
                ],
            ],
        )
        self.assertEqual(
            commands,
            [
                [
                    "llama-server",
                    "--hf-repo",
                    "ggml-org/gemma-3n-E4B-it-GGUF",
                    "--hf-file",
                    "gemma-3n-E4B-it-Q8_0.gguf",
                    "--alias",
                    "google/gemma-3n-E4B-it",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8080",
                ]
            ],
        )
        self.assertEqual(warmed_urls, ["http://127.0.0.1:8080/v1"])


if __name__ == "__main__":
    unittest.main()

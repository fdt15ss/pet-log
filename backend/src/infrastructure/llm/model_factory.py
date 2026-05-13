from __future__ import annotations

import logging
import os
from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar, cast

from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

from langchain_openai import ChatOpenAI

from infrastructure.llm.local_runtime import ensure_local_gemma_runtime, local_gemma_base_url
from infrastructure.llm.local_settings import local_gemma_api_key, local_gemma_model

logger = logging.getLogger(__name__)


DEFAULT_GPT_FALLBACK_MODEL = "gpt-5-mini"
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

TRANSIENT_LLM_ERRORS: tuple[type[BaseException], ...] = (
    TimeoutError,
    ConnectionError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)


class LLMModel(Protocol):
    def invoke(self, messages: list[object]) -> object:
        raise NotImplementedError

    def with_fallbacks(
        self,
        fallbacks: Sequence[object],
        *,
        exceptions_to_handle: tuple[type[BaseException], ...],
        exception_key: str | None = None,
    ) -> LLMModel:
        raise NotImplementedError


ModelT = TypeVar("ModelT", bound=LLMModel)
ModelFactory = Callable[[str, str, float], ModelT]


def is_local_gemma_enabled() -> bool:
    return bool(os.environ.get("GEMMA_BASE_URL") or os.environ.get("LOCAL_LLM_AUTOSTART"))


def is_gemini_model(model: str) -> bool:
    return model.startswith("gemini-")


def gemini_api_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")


def gpt_fallback_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "")


def require_local_or_gpt_api_key(provider_name: str, provider_api_key: str = "") -> None:
    if not provider_api_key and not gpt_fallback_api_key():
        raise RuntimeError(f"OPENAI_API_KEY is required to use {provider_name}.")


def build_chat_gemini_model(model: str, api_key: str, timeout: float) -> LLMModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key or gemini_api_key(),
        request_timeout=timeout,
    )


def build_chat_model(model: str, api_key: str, timeout: float) -> LLMModel:
    if is_gemini_model(model):
        return build_chat_gemini_model(model, api_key, timeout)
    return build_chat_openai_model(model, api_key, timeout)


def build_chat_openai_model(model: str, api_key: str, timeout: float) -> ChatOpenAI:
    kwargs: dict[str, object] = {
        "model": model,
        "api_key": api_key,
        "timeout": timeout,
    }

    if is_local_gemma_enabled() and model == local_gemma_model():
        ensure_local_gemma_runtime()
        kwargs["base_url"] = local_gemma_base_url()
        kwargs["use_responses_api"] = False
    else:
        kwargs["use_responses_api"] = True

    return ChatOpenAI(**kwargs)


def build_primary_with_gpt_fallback(
    *,
    provider_model: str,
    provider_api_key: str,
    fallback_model: str | None,
    timeout: float,
    model_factory: ModelFactory[ModelT],
) -> ModelT:
    # Fallback chain: GPT → Gemini → Gemma4
    primary = model_factory(provider_model, provider_api_key, timeout)
    fallbacks: list[ModelT] = []

    # Explicit GPT-tier fallback (skip if it matches the local Gemma model to avoid duplicates)
    if fallback_model and fallback_model != local_gemma_model():
        fallbacks.append(model_factory(fallback_model, provider_api_key, timeout))

    # Gemini fallback (auto-added when GEMINI_API_KEY or GOOGLE_API_KEY is set)
    _gemini_key = gemini_api_key()
    if _gemini_key:
        fallbacks.append(model_factory(DEFAULT_GEMINI_MODEL, _gemini_key, timeout))

    # Local Gemma fallback (auto-added when GEMMA_BASE_URL or LOCAL_LLM_AUTOSTART is set)
    if is_local_gemma_enabled():
        ensure_local_gemma_runtime()
        fallbacks.append(model_factory(local_gemma_model(), local_gemma_api_key(), timeout))

    chain = [provider_model] + [
        _extra_fallback_model_name(fallback_model),
        DEFAULT_GEMINI_MODEL if gemini_api_key() else None,
        local_gemma_model() if is_local_gemma_enabled() else None,
    ]
    logger.info("LLM chain: %s", " → ".join(m for m in chain if m))

    if not fallbacks:
        return primary
    return cast(ModelT, primary.with_fallbacks(fallbacks, exceptions_to_handle=TRANSIENT_LLM_ERRORS))


def _extra_fallback_model_name(fallback_model: str | None) -> str | None:
    if fallback_model and fallback_model != local_gemma_model():
        return fallback_model
    return None

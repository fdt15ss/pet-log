from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar, cast

from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

from langchain_openai import ChatOpenAI

from infrastructure.llm.local_runtime import ensure_local_gemma_runtime, local_gemma_base_url
from infrastructure.llm.local_settings import local_gemma_api_key, local_gemma_model


DEFAULT_GPT_FALLBACK_MODEL = "gpt-5-mini"

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


def gpt_fallback_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "")


def require_local_or_gpt_api_key(provider_name: str, provider_api_key: str = "") -> None:
    if is_local_gemma_enabled():
        return
    if not provider_api_key and not gpt_fallback_api_key():
        raise RuntimeError(f"OPENAI_API_KEY is required to use {provider_name}.")


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
    if is_local_gemma_enabled():
        primary_model = model_factory(local_gemma_model(), local_gemma_api_key(), timeout)
        gpt_model = fallback_model or provider_model
        if not gpt_model or not gpt_fallback_api_key():
            return primary_model
        return cast(
            ModelT,
            primary_model.with_fallbacks(
                [model_factory(gpt_model, gpt_fallback_api_key(), timeout)],
                exceptions_to_handle=TRANSIENT_LLM_ERRORS,
            ),
        )

    primary_model = model_factory(provider_model, provider_api_key, timeout)
    if not fallback_model:
        return primary_model

    return cast(
        ModelT,
        primary_model.with_fallbacks(
            [model_factory(fallback_model, provider_api_key, timeout)],
            exceptions_to_handle=TRANSIENT_LLM_ERRORS,
        ),
    )

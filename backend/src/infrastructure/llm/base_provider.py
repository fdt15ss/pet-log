from __future__ import annotations

import os
from collections.abc import Callable
from typing import Generic

from infrastructure.llm.model_factory import ModelT
from infrastructure.llm.provider_config import LLMProviderConfig


class BaseLLMProvider(Generic[ModelT]):
    def __init__(
        self,
        *,
        config: LLMProviderConfig,
        model_factory: Callable[[str, str, float], ModelT],
        model: ModelT | None = None,
    ) -> None:
        self._config = config
        self._model_factory = model_factory
        self._model = model
        if should_eager_load_llm() and self._model is None:
            self._config.require_credentials()
            self._llm()

    def _invoke_llm(self, messages: list[object]) -> object:
        self._config.require_credentials()
        return self._llm().invoke(messages)

    def _llm(self) -> ModelT:
        if self._model is None:
            self._model = self._config.build_model(self._model_factory)
        return self._model


def should_eager_load_llm() -> bool:
    return os.environ.get("LLM_EAGER_LOAD", "").lower() in {"1", "true", "yes"}

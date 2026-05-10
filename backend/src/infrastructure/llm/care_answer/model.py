from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from infrastructure.llm.model_factory import build_chat_openai_model


DEFAULT_CARE_ANSWER_MODEL = "gpt-5-mini"


class CareAnswerModel(Protocol):
    def invoke(self, messages: list[tuple[str, str]]) -> object:
        raise NotImplementedError


CareAnswerModelFactory = Callable[[str, str, float], CareAnswerModel]


def build_care_answer_model(model: str, api_key: str, timeout: float) -> CareAnswerModel:
    return build_chat_openai_model(model, api_key, timeout)

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from langchain_openai import ChatOpenAI


DEFAULT_CARE_ANSWER_MODEL = "gpt-5-mini"


class CareAnswerModel(Protocol):
    def invoke(self, messages: list[tuple[str, str]]) -> object:
        raise NotImplementedError


CareAnswerModelFactory = Callable[[str, str, float], CareAnswerModel]


def build_care_answer_model(model: str, api_key: str, timeout: float) -> CareAnswerModel:
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        timeout=timeout,
        use_responses_api=True,
    )

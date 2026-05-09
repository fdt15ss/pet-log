from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from langchain_openai import ChatOpenAI

from infrastructure.llm.image_record_understanding.schema import ImageRecordUnderstandingOutput


DEFAULT_IMAGE_RECORD_UNDERSTANDING_MODEL = "gpt-5-mini"


class ImageRecordUnderstandingModel(Protocol):
    def invoke(self, messages: list[object]) -> object:
        raise NotImplementedError


ImageRecordUnderstandingModelFactory = Callable[[str, str, float], ImageRecordUnderstandingModel]


def build_image_record_understanding_model(
    model: str,
    api_key: str,
    timeout: float,
) -> ImageRecordUnderstandingModel:
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        timeout=timeout,
        use_responses_api=True,
    )
    return llm.with_structured_output(
        ImageRecordUnderstandingOutput,
        method="json_schema",
        strict=True,
    )

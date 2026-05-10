from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from infrastructure.llm.model_factory import build_chat_openai_model
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
    llm = build_chat_openai_model(model, api_key, timeout)
    return llm.with_structured_output(
        ImageRecordUnderstandingOutput,
        method="json_schema",
        strict=True,
    )

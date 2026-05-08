from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


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
    raise NotImplementedError

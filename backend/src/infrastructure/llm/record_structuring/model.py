from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

from infrastructure.llm.model_factory import build_chat_openai_model
from infrastructure.llm.record_structuring.schema import StructuredRecordBatchOutput


DEFAULT_RECORD_STRUCTURING_MODEL = "gpt-5-mini"


class StructuredRecordBatchModel(Protocol):
    def invoke(self, messages: list[tuple[str, str]]) -> object:
        raise NotImplementedError

    def with_fallbacks(
        self,
        fallbacks: Sequence[StructuredRecordBatchModel],
        *,
        exceptions_to_handle: tuple[type[BaseException], ...],
        exception_key: str | None = None,
    ) -> StructuredRecordBatchModel:
        raise NotImplementedError


StructuredRecordBatchModelFactory = Callable[[str, str, float], StructuredRecordBatchModel]


def build_record_structuring_model(model: str, api_key: str, timeout: float) -> StructuredRecordBatchModel:
    llm = build_chat_openai_model(model, api_key, timeout)
    return llm.with_structured_output(
        StructuredRecordBatchOutput,
        method="json_schema",
        strict=True,
    )

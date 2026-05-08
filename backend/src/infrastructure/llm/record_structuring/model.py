from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from langchain_openai import ChatOpenAI

from infrastructure.llm.record_structuring.schema import StructuredRecordBatchOutput


DEFAULT_RECORD_STRUCTURING_MODEL = "gpt-5-mini"


class StructuredRecordBatchModel(Protocol):
    def invoke(self, messages: list[tuple[str, str]]) -> object:
        raise NotImplementedError


StructuredRecordBatchModelFactory = Callable[[str, str, float], StructuredRecordBatchModel]


def build_record_structuring_model(model: str, api_key: str, timeout: float) -> StructuredRecordBatchModel:
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        timeout=timeout,
        use_responses_api=True,
    )
    return llm.with_structured_output(
        StructuredRecordBatchOutput,
        method="json_schema",
        strict=True,
    )

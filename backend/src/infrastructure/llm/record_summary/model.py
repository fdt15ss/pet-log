from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from langchain_openai import ChatOpenAI

from infrastructure.llm.record_summary.schema import RecordSummaryOutput


DEFAULT_RECORD_SUMMARY_MODEL = "gpt-5-mini"


class StructuredRecordSummaryModel(Protocol):
    def invoke(self, messages: list[tuple[str, str]]) -> object:
        raise NotImplementedError


StructuredRecordSummaryModelFactory = Callable[[str, str, float], StructuredRecordSummaryModel]


def build_record_summary_model(model: str, api_key: str, timeout: float) -> StructuredRecordSummaryModel:
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        timeout=timeout,
        use_responses_api=True,
    )
    return llm.with_structured_output(
        RecordSummaryOutput,
        method="json_schema",
        strict=True,
    )

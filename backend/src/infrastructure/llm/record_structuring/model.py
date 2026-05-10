from __future__ import annotations

from infrastructure.llm.model_factory import LLMModel, build_chat_openai_model
from infrastructure.llm.record_structuring.schema import StructuredRecordBatchOutput


DEFAULT_RECORD_STRUCTURING_MODEL = "gpt-5-mini"


def build_record_structuring_model(model: str, api_key: str, timeout: float) -> LLMModel:
    llm = build_chat_openai_model(model, api_key, timeout)
    return llm.with_structured_output(
        StructuredRecordBatchOutput,
        method="json_schema",
        strict=True,
    )

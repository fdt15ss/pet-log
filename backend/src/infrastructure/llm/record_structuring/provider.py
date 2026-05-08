from __future__ import annotations

import os

from application.dto import PetLogAgentInput
from application.interfaces import RecordStructurerInterface
from domain.models import StructuredRecordBatch
from infrastructure.llm.record_structuring.mapper import to_structured_record_batch
from infrastructure.llm.record_structuring.model import (
    DEFAULT_RECORD_STRUCTURING_MODEL,
    StructuredRecordBatchModel,
    StructuredRecordBatchModelFactory,
    build_record_structuring_model,
)
from infrastructure.llm.record_structuring.prompt import build_record_structuring_messages


class RecordStructurer(RecordStructurerInterface):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        model_factory: StructuredRecordBatchModelFactory = build_record_structuring_model,
        structured_model: StructuredRecordBatchModel | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get("OPENAI_RECORD_STRUCTURING_MODEL", DEFAULT_RECORD_STRUCTURING_MODEL)
        self._timeout = timeout
        self._model_factory = model_factory
        self._structured_model = structured_model

    def structure(self, input: PetLogAgentInput) -> StructuredRecordBatch:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required to use RecordStructurer.")

        result = self._structured_llm().invoke(build_record_structuring_messages(input))
        return to_structured_record_batch(result)

    def _structured_llm(self) -> StructuredRecordBatchModel:
        if self._structured_model is None:
            self._structured_model = self._model_factory(self._model, self._api_key, self._timeout)
        return self._structured_model

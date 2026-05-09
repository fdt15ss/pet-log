from __future__ import annotations

import os

from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError

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


TRANSIENT_RECORD_STRUCTURING_ERRORS: tuple[type[BaseException], ...] = (
    TimeoutError,
    ConnectionError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)


class RecordStructurer(RecordStructurerInterface):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
        timeout: float = 30.0,
        model_factory: StructuredRecordBatchModelFactory = build_record_structuring_model,
        structured_model: StructuredRecordBatchModel | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get("OPENAI_RECORD_STRUCTURING_MODEL", DEFAULT_RECORD_STRUCTURING_MODEL)
        self._fallback_model = fallback_model or os.environ.get("OPENAI_RECORD_STRUCTURING_FALLBACK_MODEL") or None
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
            primary_model = self._model_factory(self._model, self._api_key, self._timeout)
            if self._fallback_model:
                fallback_model = self._model_factory(self._fallback_model, self._api_key, self._timeout)
                primary_model = primary_model.with_fallbacks(
                    [fallback_model],
                    exceptions_to_handle=TRANSIENT_RECORD_STRUCTURING_ERRORS,
                )
            self._structured_model = primary_model
        return self._structured_model

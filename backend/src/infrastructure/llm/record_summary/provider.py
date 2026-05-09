from __future__ import annotations

import os

from application.dto import RecordSummaryResult
from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder
from infrastructure.llm.record_summary.mapper import to_record_summary_result
from infrastructure.llm.record_summary.model import (
    DEFAULT_RECORD_SUMMARY_MODEL,
    StructuredRecordSummaryModel,
    StructuredRecordSummaryModelFactory,
    build_record_summary_model,
)
from infrastructure.llm.record_summary.prompt import build_record_summary_messages


class RecordSummaryProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        model_factory: StructuredRecordSummaryModelFactory = build_record_summary_model,
        structured_model: StructuredRecordSummaryModel | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get("OPENAI_RECORD_SUMMARY_MODEL", DEFAULT_RECORD_SUMMARY_MODEL)
        self._timeout = timeout
        self._model_factory = model_factory
        self._structured_model = structured_model

    def summarize(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> RecordSummaryResult:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required to use RecordSummaryProvider.")

        result = self._structured_llm().invoke(
            build_record_summary_messages(pet, records, context, due_items)
        )
        return to_record_summary_result(result)

    def _structured_llm(self) -> StructuredRecordSummaryModel:
        if self._structured_model is None:
            self._structured_model = self._model_factory(self._model, self._api_key, self._timeout)
        return self._structured_model

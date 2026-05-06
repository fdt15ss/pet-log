from __future__ import annotations

from application.dto import PetLogAgentInput, PetLogAgentResult
from application.interfaces import (
    ContextAnalysisAgentInterface,
    PetLogAgentPipelineInterface,
    RecordHistoryReaderInterface,
    RecordRepositoryInterface,
    RecordStructuringAgentInterface,
    ReminderAgentInterface,
    RiskDetectionAgentInterface,
    ScheduleContextReaderInterface,
    SuggestionAgentInterface,
)


class PetLogAgentPipeline(PetLogAgentPipelineInterface):
    def __init__(
        self,
        record_structuring_agent: RecordStructuringAgentInterface,
        record_history_reader: RecordHistoryReaderInterface,
        schedule_context_reader: ScheduleContextReaderInterface,
        context_analysis_agent: ContextAnalysisAgentInterface,
        risk_detection_agent: RiskDetectionAgentInterface,
        record_repository: RecordRepositoryInterface,
        suggestion_agent: SuggestionAgentInterface,
        reminder_agent: ReminderAgentInterface,
        lookback_days: int = 30,
        days_ahead: int = 14,
    ) -> None:
        self._record_structuring_agent = record_structuring_agent
        self._record_history_reader = record_history_reader
        self._schedule_context_reader = schedule_context_reader
        self._context_analysis_agent = context_analysis_agent
        self._risk_detection_agent = risk_detection_agent
        self._record_repository = record_repository
        self._suggestion_agent = suggestion_agent
        self._reminder_agent = reminder_agent
        self._lookback_days = lookback_days
        self._days_ahead = days_ahead

    def handle(self, input: PetLogAgentInput) -> PetLogAgentResult:
        candidate = self._record_structuring_agent.structure(input)
        recent_records = self._record_history_reader.list_recent(input.pet.id, self._lookback_days)
        due_items = self._schedule_context_reader.list_due_items(input.pet.id, self._days_ahead)
        context = self._context_analysis_agent.analyze(input.pet, recent_records, due_items)
        safety_notices = self._risk_detection_agent.detect(input.text, recent_records)

        if candidate.needs_confirmation and not input.confirm:
            return PetLogAgentResult(
                candidate=candidate,
                context_analysis=context,
                safety_notices=safety_notices,
            )

        saved_record = self._record_repository.save_candidate(input.pet.id, candidate)
        suggestions = self._suggestion_agent.suggest(input.pet, context, safety_notices)
        reminders = self._reminder_agent.plan(input.pet, recent_records + (saved_record,), due_items)

        return PetLogAgentResult(
            candidate=candidate,
            saved_record=saved_record,
            context_analysis=context,
            safety_notices=safety_notices,
            suggestions=suggestions,
            reminders=reminders,
        )

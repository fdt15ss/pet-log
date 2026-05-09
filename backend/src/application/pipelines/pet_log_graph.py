from __future__ import annotations

import logging
import warnings
from collections.abc import Iterator
from typing import Literal, TypedDict

from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

warnings.simplefilter("ignore", LangChainPendingDeprecationWarning)

from langgraph.graph import END, START, StateGraph  # noqa: E402

from application.dto import PetLogAgentInput, PetLogAgentResult  # noqa: E402
from application.interfaces import (  # noqa: E402
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
from domain.models import (  # noqa: E402
    CareSuggestion,
    ContextAnalysisResult,
    PetRecord,
    PlannedReminder,
    SafetyNotice,
    StructuredRecordBatch,
)


logger = logging.getLogger(__name__)


class PetLogAgentState(TypedDict, total=False):
    input: PetLogAgentInput
    record_batch: StructuredRecordBatch
    recent_records: tuple[PetRecord, ...]
    due_items: tuple[PlannedReminder, ...]
    context_analysis: ContextAnalysisResult
    safety_notices: tuple[SafetyNotice, ...]
    saved_records: tuple[PetRecord, ...]
    suggestions: tuple[CareSuggestion, ...]
    reminders: tuple[PlannedReminder, ...]
    result: PetLogAgentResult


class LangGraphPetLogAgentPipeline(PetLogAgentPipelineInterface):
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
        self._graph = self._build_graph()

    def handle(self, input: PetLogAgentInput) -> PetLogAgentResult:
        result: PetLogAgentResult | None = None
        for update in self.stream_updates(input):
            self._log_update(update)
            for node_state in update.values():
                if "result" in node_state:
                    result = node_state["result"]
        if result is None:
            raise RuntimeError("Pet log graph completed without result")
        return result

    def stream_updates(self, input: PetLogAgentInput) -> Iterator[dict[str, PetLogAgentState]]:
        return self._graph.stream({"input": input}, stream_mode="updates")

    def _log_update(self, update: dict[str, PetLogAgentState]) -> None:
        for node_name, node_state in update.items():
            updated_keys = ",".join(sorted(node_state.keys()))
            logger.info(
                "pet_log_agent_graph_node_completed node=%s updated_keys=%s",
                node_name,
                updated_keys,
            )

    def _build_graph(self):
        graph = StateGraph(PetLogAgentState)
        graph.add_node("structure_record", self._structure_record)
        graph.add_node("load_context", self._load_context)
        graph.add_node("analyze_context", self._analyze_context)
        graph.add_node("detect_risk", self._detect_risk)
        graph.add_node("build_confirmation_result", self._build_confirmation_result)
        graph.add_node("save_records", self._save_records)
        graph.add_node("suggest_care", self._suggest_care)
        graph.add_node("plan_reminders", self._plan_reminders)
        graph.add_node("build_saved_result", self._build_saved_result)

        graph.add_edge(START, "structure_record")
        graph.add_edge("structure_record", "load_context")
        graph.add_edge("load_context", "analyze_context")
        graph.add_edge("analyze_context", "detect_risk")
        graph.add_conditional_edges(
            "detect_risk",
            self._route_after_risk_detection,
            {
                "confirm": "build_confirmation_result",
                "save": "save_records",
            },
        )
        graph.add_edge("build_confirmation_result", END)
        graph.add_edge("save_records", "suggest_care")
        graph.add_edge("suggest_care", "plan_reminders")
        graph.add_edge("plan_reminders", "build_saved_result")
        graph.add_edge("build_saved_result", END)
        return graph.compile()

    def _structure_record(self, state: PetLogAgentState) -> PetLogAgentState:
        return {"record_batch": self._record_structuring_agent.structure(state["input"])}

    def _load_context(self, state: PetLogAgentState) -> PetLogAgentState:
        input = state["input"]
        return {
            "recent_records": self._record_history_reader.list_recent(input.pet.id, self._lookback_days),
            "due_items": self._schedule_context_reader.list_due_items(input.pet.id, self._days_ahead),
        }

    def _analyze_context(self, state: PetLogAgentState) -> PetLogAgentState:
        return {
            "context_analysis": self._context_analysis_agent.analyze(
                state["input"].pet,
                state["recent_records"],
                state["due_items"],
            )
        }

    def _detect_risk(self, state: PetLogAgentState) -> PetLogAgentState:
        return {
            "safety_notices": self._risk_detection_agent.detect(
                state["input"].text,
                state["recent_records"],
            )
        }

    def _route_after_risk_detection(self, state: PetLogAgentState) -> Literal["confirm", "save"]:
        input = state["input"]
        if input.source == "ai_preview" or (state["record_batch"].needs_confirmation and not input.confirm):
            return "confirm"
        return "save"

    def _build_confirmation_result(self, state: PetLogAgentState) -> PetLogAgentState:
        return {
            "result": PetLogAgentResult(
                candidates=state["record_batch"].candidates,
                context_analysis=state["context_analysis"],
                safety_notices=state["safety_notices"],
            )
        }

    def _save_records(self, state: PetLogAgentState) -> PetLogAgentState:
        input = state["input"]
        return {
            "saved_records": tuple(
                self._record_repository.save_candidate(input.pet.id, candidate, source=input.source)
                for candidate in state["record_batch"].candidates
            )
        }

    def _suggest_care(self, state: PetLogAgentState) -> PetLogAgentState:
        return {
            "suggestions": self._suggestion_agent.suggest(
                state["input"].pet,
                state["context_analysis"],
                state["safety_notices"],
            )
        }

    def _plan_reminders(self, state: PetLogAgentState) -> PetLogAgentState:
        return {
            "reminders": self._reminder_agent.plan(
                state["input"].pet,
                state["recent_records"] + state["saved_records"],
                state["due_items"],
            )
        }

    def _build_saved_result(self, state: PetLogAgentState) -> PetLogAgentState:
        return {
            "result": PetLogAgentResult(
                candidates=state["record_batch"].candidates,
                saved_records=state["saved_records"],
                context_analysis=state["context_analysis"],
                safety_notices=state["safety_notices"],
                suggestions=state["suggestions"],
                reminders=state["reminders"],
            )
        }

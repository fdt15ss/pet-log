from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any, Literal, Protocol

from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from application.dto import RecordSummaryResult
from application.interfaces import RecordSummaryProviderInterface
from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder, SafetyNotice


DEFAULT_RECORD_SUMMARY_MODEL = "gpt-5-mini"


class LangChainAgent(Protocol):
    def invoke(self, payload: dict[str, object]) -> dict[str, object]:
        raise NotImplementedError


LangChainAgentFactory = Callable[[str, str, float], LangChainAgent]


class RecordSummarySafetyNoticeOutput(BaseModel):
    level: Literal["info", "notice", "alert"]
    message: str


class RecordSummaryOutput(BaseModel):
    summary: str
    record_ids: list[str]
    highlights: list[str]
    behavior_patterns: list[str]
    missing_record_notes: list[str]
    safety_notice: RecordSummarySafetyNoticeOutput | None


def build_record_summary_langchain_agent(model: str, api_key: str, timeout: float) -> LangChainAgent:
    llm = ChatOpenAI(
        model=model,
        api_key=api_key,
        timeout=timeout,
        use_responses_api=True,
    )
    return create_agent(
        model=llm,
        tools=[],
        system_prompt=(
            "반려동물 기록을 보호자가 이해하기 쉬운 한국어로 요약하세요. "
            "진단을 단정하지 마세요. 위험 신호가 있으면 safety_notice로 분리하고 "
            "병원 상담이 필요한 가능성만 조심스럽게 표현하세요."
        ),
        response_format=ProviderStrategy(RecordSummaryOutput),
        name="record_summary_agent",
    )


class RecordSummaryProvider(RecordSummaryProviderInterface):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        agent_factory: LangChainAgentFactory = build_record_summary_langchain_agent,
        langchain_agent: LangChainAgent | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get("OPENAI_RECORD_SUMMARY_MODEL", DEFAULT_RECORD_SUMMARY_MODEL)
        self._timeout = timeout
        self._agent_factory = agent_factory
        self._langchain_agent = langchain_agent

    def summarize(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> RecordSummaryResult:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required to use RecordSummaryProvider.")

        result = self._agent().invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": self._prompt(pet, records, context, due_items),
                    }
                ]
            }
        )
        structured_response = result.get("structured_response")
        if structured_response is None:
            raise RuntimeError("LangChain record summary agent did not return structured_response.")
        return self._to_result(structured_response)

    def _agent(self) -> LangChainAgent:
        if self._langchain_agent is None:
            self._langchain_agent = self._agent_factory(self._model, self._api_key, self._timeout)
        return self._langchain_agent

    def _prompt(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> str:
        return (
            "다음 데이터를 기반으로 RecordSummaryResult 형식의 요약을 작성하세요. "
            "진단을 단정하지 마세요.\n\n"
            + json.dumps(
                {
                    "pet": self._pet_payload(pet),
                    "records": [self._record_payload(record) for record in records],
                    "context": self._context_payload(context),
                    "due_items": [self._due_item_payload(item) for item in due_items],
                },
                ensure_ascii=False,
            )
        )

    def _to_result(self, value: object) -> RecordSummaryResult:
        if isinstance(value, BaseModel):
            parsed = value.model_dump()
        elif isinstance(value, dict):
            parsed = value
        else:
            raise RuntimeError("LangChain structured_response had an invalid shape.")

        safety_notice = parsed.get("safety_notice")
        return RecordSummaryResult(
            summary=str(parsed["summary"]),
            record_ids=tuple(str(item) for item in parsed["record_ids"]),
            highlights=tuple(str(item) for item in parsed["highlights"]),
            behavior_patterns=tuple(str(item) for item in parsed["behavior_patterns"]),
            missing_record_notes=tuple(str(item) for item in parsed["missing_record_notes"]),
            safety_notice=self._safety_notice(safety_notice),
        )

    def _safety_notice(self, value: object) -> SafetyNotice | None:
        if value is None:
            return None
        if isinstance(value, BaseModel):
            value = value.model_dump()
        if not isinstance(value, dict):
            raise RuntimeError("LangChain safety_notice output was not an object.")
        level = value.get("level")
        message = value.get("message")
        if level not in ("info", "notice", "alert") or not isinstance(message, str):
            raise RuntimeError("LangChain safety_notice output had an invalid shape.")
        return SafetyNotice(level=level, message=message)

    def _pet_payload(self, pet: PetProfile) -> dict[str, object]:
        return {
            "id": pet.id,
            "name": pet.name,
            "breed": pet.breed,
            "species": pet.species,
            "age_label": pet.age_label,
            "personality": pet.personality,
            "notes": list(pet.notes),
        }

    def _record_payload(self, record: PetRecord) -> dict[str, object]:
        return {
            "id": record.id,
            "pet_id": record.pet_id,
            "category": record.category,
            "title": record.title,
            "detail": record.detail,
            "status": record.status,
            "recorded_at": record.recorded_at,
            "source": record.source,
        }

    def _context_payload(self, context: ContextAnalysisResult) -> dict[str, object]:
        return {
            "insights": [self._insight_payload(insight) for insight in context.insights],
            "missing_record_insights": [
                self._insight_payload(insight) for insight in context.missing_record_insights
            ],
        }

    def _insight_payload(self, insight: Any) -> dict[str, object]:
        return {
            "severity": insight.severity,
            "title": insight.title,
            "reason": insight.reason,
            "source_record_ids": list(insight.source_record_ids),
        }

    def _due_item_payload(self, item: PlannedReminder) -> dict[str, object]:
        return {
            "title": item.title,
            "due_date": item.due_date,
            "reason": item.reason,
        }

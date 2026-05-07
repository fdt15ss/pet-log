from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

from application.dto import RecordSummaryResult
from application.interfaces import RecordSummaryProviderInterface
from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder, SafetyNotice


OpenAITransport = Callable[[str, dict[str, str], dict[str, object], float], dict[str, object]]


DEFAULT_OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_RECORD_SUMMARY_MODEL = "gpt-5-mini"


def _default_transport(
    endpoint: str,
    headers: dict[str, str],
    payload: dict[str, object],
    timeout: float,
) -> dict[str, object]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI record summary request failed: {error.code} {error_body}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"OpenAI record summary request failed: {error}") from error

    parsed = json.loads(response_body)
    if not isinstance(parsed, dict):
        raise RuntimeError("OpenAI record summary response was not a JSON object.")
    return parsed


class RecordSummaryProvider(RecordSummaryProviderInterface):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        endpoint: str = DEFAULT_OPENAI_RESPONSES_ENDPOINT,
        timeout: float = 30.0,
        transport: OpenAITransport = _default_transport,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get("OPENAI_RECORD_SUMMARY_MODEL", DEFAULT_RECORD_SUMMARY_MODEL)
        self._endpoint = endpoint
        self._timeout = timeout
        self._transport = transport

    def summarize(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> RecordSummaryResult:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required to use RecordSummaryProvider.")

        response = self._transport(
            self._endpoint,
            {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            self._build_payload(pet, records, context, due_items),
            self._timeout,
        )
        return self._parse_result(response)

    def _build_payload(
        self,
        pet: PetProfile,
        records: tuple[PetRecord, ...],
        context: ContextAnalysisResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> dict[str, object]:
        return {
            "model": self._model,
            "instructions": (
                "반려동물 기록을 보호자가 이해하기 쉬운 한국어로 요약하세요. "
                "진단을 단정하지 마세요. 위험 신호가 있으면 safety_notice로 분리하고 "
                "병원 상담이 필요한 가능성만 조심스럽게 표현하세요."
            ),
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {
                                    "pet": self._pet_payload(pet),
                                    "records": [self._record_payload(record) for record in records],
                                    "context": self._context_payload(context),
                                    "due_items": [self._due_item_payload(item) for item in due_items],
                                },
                                ensure_ascii=False,
                            ),
                        }
                    ],
                }
            ],
            "text": {"format": self._response_format()},
            "max_output_tokens": 1200,
        }

    def _parse_result(self, response: dict[str, object]) -> RecordSummaryResult:
        output_text = self._extract_output_text(response)
        parsed = json.loads(output_text)
        if not isinstance(parsed, dict):
            raise RuntimeError("OpenAI record summary output was not a JSON object.")

        safety_notice = parsed.get("safety_notice")
        return RecordSummaryResult(
            summary=str(parsed.get("summary", "")),
            record_ids=tuple(str(item) for item in parsed.get("record_ids", ())),
            highlights=tuple(str(item) for item in parsed.get("highlights", ())),
            behavior_patterns=tuple(str(item) for item in parsed.get("behavior_patterns", ())),
            missing_record_notes=tuple(str(item) for item in parsed.get("missing_record_notes", ())),
            safety_notice=self._safety_notice(safety_notice),
        )

    def _extract_output_text(self, response: dict[str, object]) -> str:
        output_text = response.get("output_text")
        if isinstance(output_text, str):
            return output_text

        output = response.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for content_item in content:
                    if isinstance(content_item, dict) and isinstance(content_item.get("text"), str):
                        return str(content_item["text"])

        raise RuntimeError("OpenAI record summary response did not contain output text.")

    def _safety_notice(self, value: object) -> SafetyNotice | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise RuntimeError("OpenAI safety_notice output was not an object.")
        level = value.get("level")
        message = value.get("message")
        if level not in ("info", "notice", "alert") or not isinstance(message, str):
            raise RuntimeError("OpenAI safety_notice output had an invalid shape.")
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

    def _response_format(self) -> dict[str, object]:
        return {
            "type": "json_schema",
            "name": "record_summary_result",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "record_ids": {"type": "array", "items": {"type": "string"}},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                    "behavior_patterns": {"type": "array", "items": {"type": "string"}},
                    "missing_record_notes": {"type": "array", "items": {"type": "string"}},
                    "safety_notice": {
                        "anyOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "level": {"type": "string", "enum": ["info", "notice", "alert"]},
                                    "message": {"type": "string"},
                                },
                                "required": ["level", "message"],
                                "additionalProperties": False,
                            },
                            {"type": "null"},
                        ]
                    },
                },
                "required": [
                    "summary",
                    "record_ids",
                    "highlights",
                    "behavior_patterns",
                    "missing_record_notes",
                    "safety_notice",
                ],
                "additionalProperties": False,
            },
        }

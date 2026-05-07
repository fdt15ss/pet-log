from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


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

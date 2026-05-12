from __future__ import annotations

import hashlib

from application.dto import NotificationCandidate
from domain.models import ContextAnalysisResult, PetProfile, PlannedReminder, SafetyNotice


class NotificationPolicy:
    def plan(
        self,
        pet: PetProfile,
        context: ContextAnalysisResult,
        safety_notices: tuple[SafetyNotice, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[NotificationCandidate, ...]:
        candidates: list[NotificationCandidate] = []

        for insight in context.missing_record_insights:
            candidates.append(NotificationCandidate(
                title=insight.title,
                message=insight.reason,
                kind="missing_record",
                dedupe_key=_key("missing_record", insight.title),
                source_record_ids=insight.source_record_ids,
            ))

        for insight in context.insights:
            if insight.severity == "alert":
                candidates.append(NotificationCandidate(
                    title=insight.title,
                    message=insight.reason,
                    kind="risk",
                    dedupe_key=_key("risk", insight.title),
                    source_record_ids=insight.source_record_ids,
                ))
            else:
                candidates.append(NotificationCandidate(
                    title=insight.title,
                    message=insight.reason,
                    kind="behavior_change",
                    dedupe_key=_key("behavior_change", insight.title),
                    source_record_ids=insight.source_record_ids,
                ))

        for notice in safety_notices:
            candidates.append(NotificationCandidate(
                title=f"{pet.name} 안전 알림",
                message=notice.message,
                kind="risk",
                dedupe_key=_key("safety", notice.message),
                safety_notice=notice,
            ))

        for item in due_items:
            candidates.append(NotificationCandidate(
                title=item.title,
                message=item.reason,
                kind="schedule",
                dedupe_key=_key("schedule", item.title + item.due_date),
                due_date=item.due_date,
            ))

        return tuple(candidates)


def _key(prefix: str, content: str) -> str:
    digest = hashlib.sha256(content.encode()).hexdigest()[:12]
    return f"{prefix}:{digest}"

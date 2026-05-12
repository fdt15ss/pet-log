from __future__ import annotations

from domain.models import CareInsight, CareSuggestion, PetProfile


class SuggestionComposer:
    def compose(self, pet: PetProfile, insights: tuple[CareInsight, ...]) -> tuple[CareSuggestion, ...]:
        return tuple(
            CareSuggestion(
                title=insight.title,
                action="기록 확인하기" if insight.severity == "info" else "지금 확인하기",
                reason=insight.reason,
                severity=insight.severity,
                source_record_ids=insight.source_record_ids,
            )
            for insight in insights
        )

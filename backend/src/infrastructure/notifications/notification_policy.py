from __future__ import annotations

from application.dto import NotificationCandidate
from application.interfaces import NotificationPolicyInterface
from domain.models import ContextAnalysisResult, PetProfile, PlannedReminder, SafetyNotice


class NotificationPolicy(NotificationPolicyInterface):
    def plan(
        self,
        pet: PetProfile,
        context: ContextAnalysisResult,
        safety_notices: tuple[SafetyNotice, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[NotificationCandidate, ...]:
        raise NotImplementedError

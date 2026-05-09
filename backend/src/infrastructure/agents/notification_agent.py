from __future__ import annotations

from application.dto import NotificationCandidate
from application.interfaces import NotificationAgentInterface, NotificationPolicyInterface
from domain.models import ContextAnalysisResult, PetProfile, PlannedReminder, SafetyNotice


class NotificationAgent(NotificationAgentInterface):
    def __init__(self, notification_policy: NotificationPolicyInterface) -> None:
        self._notification_policy = notification_policy

    def plan(
        self,
        pet: PetProfile,
        context: ContextAnalysisResult,
        safety_notices: tuple[SafetyNotice, ...],
        due_items: tuple[PlannedReminder, ...],
    ) -> tuple[NotificationCandidate, ...]:
        raise NotImplementedError

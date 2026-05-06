from __future__ import annotations

from application.dto import HomeFeedResult, PetLogAgentResult
from application.interfaces import HomeFeedComposerInterface
from domain.models import PetProfile, PlannedReminder


class HomeFeedComposer(HomeFeedComposerInterface):
    def compose(
        self,
        pet: PetProfile,
        agent_result: PetLogAgentResult,
        due_items: tuple[PlannedReminder, ...],
    ) -> HomeFeedResult:
        raise NotImplementedError

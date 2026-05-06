from __future__ import annotations

from application.interfaces import SafetyGuardInterface
from domain.models import SafetyNotice


class SafetyGuard(SafetyGuardInterface):
    def check(self, text: str) -> SafetyNotice | None:
        raise NotImplementedError

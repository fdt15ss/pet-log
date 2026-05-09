from __future__ import annotations

from application.interfaces import RiskSignalPolicyInterface
from domain.models import PetRecord, SafetyNotice


class RiskSignalPolicy(RiskSignalPolicyInterface):
    def detect_risks(self, text: str, records: tuple[PetRecord, ...]) -> tuple[SafetyNotice, ...]:
        return ()

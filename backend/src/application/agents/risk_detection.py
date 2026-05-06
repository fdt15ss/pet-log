from __future__ import annotations

from application.interfaces import RiskDetectionAgentInterface, RiskSignalPolicyInterface
from domain.models import PetRecord, SafetyNotice


class RiskDetectionAgent(RiskDetectionAgentInterface):
    def __init__(self, risk_signal_policy: RiskSignalPolicyInterface) -> None:
        self._risk_signal_policy = risk_signal_policy

    def detect(self, text: str, records: tuple[PetRecord, ...]) -> tuple[SafetyNotice, ...]:
        return self._risk_signal_policy.detect_risks(text, records)

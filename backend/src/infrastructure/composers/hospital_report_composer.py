from __future__ import annotations

from application.dto import HospitalSummaryResult
from application.interfaces import HospitalReportComposerInterface
from domain.models import PetProfile, PetRecord


class HospitalReportComposer(HospitalReportComposerInterface):
    def compose(self, pet: PetProfile, records: tuple[PetRecord, ...]) -> HospitalSummaryResult:
        raise NotImplementedError

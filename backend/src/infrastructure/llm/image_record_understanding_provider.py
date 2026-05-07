from __future__ import annotations

from application.interfaces import ImageRecordUnderstandingProviderInterface
from domain.models import PetProfile, StructuredRecordCandidate


class ImageRecordUnderstandingProvider(ImageRecordUnderstandingProviderInterface):
    def understand(
        self,
        pet: PetProfile,
        image: bytes,
        content_type: str,
        user_note: str | None = None,
    ) -> StructuredRecordCandidate:
        raise NotImplementedError

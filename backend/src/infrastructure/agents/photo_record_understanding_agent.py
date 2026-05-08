from __future__ import annotations

from application.interfaces import ImageRecordUnderstandingProviderInterface, PhotoRecordUnderstandingAgentInterface
from domain.models import PetProfile, StructuredRecordCandidate


class PhotoRecordUnderstandingAgent(PhotoRecordUnderstandingAgentInterface):
    def __init__(self, image_understanding_provider: ImageRecordUnderstandingProviderInterface) -> None:
        self._image_understanding_provider = image_understanding_provider

    def understand(
        self,
        pet: PetProfile,
        image: bytes,
        content_type: str,
        user_note: str | None = None,
    ) -> StructuredRecordCandidate:
        raise NotImplementedError

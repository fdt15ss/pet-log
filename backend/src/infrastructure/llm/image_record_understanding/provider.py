from __future__ import annotations

import os

from application.interfaces import ImageRecordUnderstandingProviderInterface
from domain.models import PetProfile, StructuredRecordCandidate
from infrastructure.llm.image_record_understanding.model import (
    DEFAULT_IMAGE_RECORD_UNDERSTANDING_MODEL,
    ImageRecordUnderstandingModel,
    ImageRecordUnderstandingModelFactory,
    build_image_record_understanding_model,
)


class ImageRecordUnderstandingProvider(ImageRecordUnderstandingProviderInterface):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        model_factory: ImageRecordUnderstandingModelFactory = build_image_record_understanding_model,
        structured_model: ImageRecordUnderstandingModel | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get(
            "OPENAI_IMAGE_RECORD_UNDERSTANDING_MODEL",
            DEFAULT_IMAGE_RECORD_UNDERSTANDING_MODEL,
        )
        self._timeout = timeout
        self._model_factory = model_factory
        self._structured_model = structured_model

    def understand(
        self,
        pet: PetProfile,
        image: bytes,
        content_type: str,
        user_note: str | None = None,
    ) -> StructuredRecordCandidate:
        raise NotImplementedError

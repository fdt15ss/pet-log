from __future__ import annotations

import os

from application.interfaces import PetPersonaResponderInterface
from domain.models import CareContext
from infrastructure.llm.pet_persona.mapper import message_content_to_text
from infrastructure.llm.pet_persona.model import (
    DEFAULT_PET_PERSONA_MODEL,
    PetPersonaModel,
    PetPersonaModelFactory,
    build_pet_persona_model,
)
from infrastructure.llm.pet_persona.prompt import build_pet_persona_messages


class PetPersonaResponder(PetPersonaResponderInterface):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
        model_factory: PetPersonaModelFactory = build_pet_persona_model,
        chat_model: PetPersonaModel | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self._model = model or os.environ.get("OPENAI_PET_PERSONA_MODEL", DEFAULT_PET_PERSONA_MODEL)
        self._timeout = timeout
        self._model_factory = model_factory
        self._chat_model = chat_model

    def respond(self, context: CareContext, message: str) -> str:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required to use PetPersonaResponder.")

        result = self._chat_llm().invoke(build_pet_persona_messages(context, message))
        return message_content_to_text(result)

    def _chat_llm(self) -> PetPersonaModel:
        if self._chat_model is None:
            self._chat_model = self._model_factory(self._model, self._api_key, self._timeout)
        return self._chat_model

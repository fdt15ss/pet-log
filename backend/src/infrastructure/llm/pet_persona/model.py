from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from infrastructure.llm.model_factory import build_chat_openai_model


DEFAULT_PET_PERSONA_MODEL = "gpt-5-mini"


class PetPersonaModel(Protocol):
    def invoke(self, messages: list[tuple[str, str]]) -> object:
        raise NotImplementedError


PetPersonaModelFactory = Callable[[str, str, float], PetPersonaModel]


def build_pet_persona_model(model: str, api_key: str, timeout: float) -> PetPersonaModel:
    return build_chat_openai_model(model, api_key, timeout)

from __future__ import annotations

from application.interfaces import PetPersonaAgentInterface, PetPersonaResponderInterface
from domain.models import CareContext


class PetPersonaAgent(PetPersonaAgentInterface):
    def __init__(self, responder: PetPersonaResponderInterface) -> None:
        self._responder = responder

    def respond(self, context: CareContext, message: str) -> str:
        return self._responder.respond(context, message)

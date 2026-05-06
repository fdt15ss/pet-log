from __future__ import annotations

from application.interfaces import PetPersonaResponderInterface
from domain.models import CareContext


class PetPersonaResponder(PetPersonaResponderInterface):
    def respond(self, context: CareContext, message: str) -> str:
        raise NotImplementedError

from __future__ import annotations

from domain.models import PetProfile


def build_image_record_understanding_messages(
    pet: PetProfile,
    image: bytes,
    content_type: str,
    user_note: str | None = None,
) -> list[object]:
    raise NotImplementedError

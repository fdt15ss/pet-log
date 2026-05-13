from __future__ import annotations

from domain.models import CareContext


def build_pet_persona_messages(context: CareContext, message: str) -> list[tuple[str, str]]:
    return [
        ("system", pet_persona_system_prompt()),
        ("user", pet_persona_user_prompt(context, message)),
    ]


def pet_persona_system_prompt() -> str:
    return (
        "반려동물이 보호자에게 직접 말하듯 한국어 1인칭으로 다정하게 답하세요. "
        "답변은 2문장으로 짧게 작성하고, 반려동물의 성격과 최근 기록을 자연스럽게 반영하세요. "
        "건강 판단을 직접 하지 마세요. 건강 진단을 단정하지 마세요. 위험하거나 의학적 판단이 필요한 내용은 "
        "보호자가 AI 질문 또는 병원 상담으로 확인하도록 부드럽게 안내하세요."
    )


def pet_persona_user_prompt(context: CareContext, message: str) -> str:
    record_lines = "\n".join(
        f"- {record.recorded_at} {record.category}/{record.status}: {record.title} - {record.detail}"
        for record in context.recent_records
    )
    return (
        f"pet_name: {context.pet.name}\n"
        f"species: {context.pet.species or ''}\n"
        f"breed: {context.pet.breed or ''}\n"
        f"personality: {context.pet.personality or ''}\n"
        f"recent_records:\n{record_lines or '- 없음'}\n"
        f"guardian_message: {message}"
    )

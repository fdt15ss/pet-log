from __future__ import annotations

import json

from application.dto import PetLogAgentInput
from infrastructure.llm.record_structuring.mapper import allowed_values_payload, input_payload


def build_record_structuring_messages(input: PetLogAgentInput) -> list[tuple[str, str]]:
    return [
        ("system", record_structuring_system_prompt()),
        ("user", record_structuring_user_prompt(input)),
    ]


def record_structuring_system_prompt() -> str:
    return (
        "반려동물 기록 입력을 저장 전 후보로 구조화하세요. "
        "여러 사건이 섞이면 후보를 나누세요. "
        "관찰된 사실만 기록하고 진단을 단정하지 마세요. "
        "확신이 낮거나 보호자 확인이 필요한 내용은 needs_confirmation을 true로 설정하세요."
    )


def record_structuring_user_prompt(input: PetLogAgentInput) -> str:
    return (
        "다음 입력을 StructuredRecordBatch 형식으로 변환하세요. "
        "category와 status는 allowed_values에 있는 값만 사용하세요.\n\n"
        + json.dumps(
            {
                "input": input_payload(input),
                "allowed_values": allowed_values_payload(),
                "splitting_examples": [
                    {
                        "text": (
                            "오늘 오전 8시에 초코가 사료 40g 중 15g만 먹고, "
                            "저녁 산책은 12분만 했고, 오른쪽 귀를 5번 긁었어."
                        ),
                        "candidates": [
                            {
                                "category": "meal",
                                "title": "식사",
                                "detail": "오전 8시에 사료 40g 중 15g만 먹음",
                                "measurements": ["오전 8시", "사료 40g", "섭취 15g"],
                            },
                            {
                                "category": "walk",
                                "title": "산책",
                                "detail": "저녁 산책을 12분만 함",
                                "measurements": ["12분"],
                            },
                            {
                                "category": "medical",
                                "title": "귀 긁음",
                                "detail": "오른쪽 귀를 5번 긁음",
                                "measurements": ["오른쪽 귀", "5번"],
                            },
                        ],
                    }
                ],
            },
            ensure_ascii=False,
        )
    )

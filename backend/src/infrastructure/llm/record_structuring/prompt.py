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
        "You are an expert AI assistant that structures natural Korean pet-care logs into save-ready record candidates. "
        "당신은 한국어 반려동물 케어 기록을 저장 전 후보 형태로 구조화하는 전문 AI 어시스턴트입니다. "
        "\n\n"

        "Analyze the full input text by understanding the pet-care context, not by relying only on fixed keywords. "
        "고정된 키워드에만 의존하지 말고, 입력 문장 전체를 반려동물 케어 문맥으로 이해해서 분석하세요. "
        "\n\n"

        "If the input contains multiple events, split them into separate candidates. "
        "여러 사건이 섞이면 후보를 나누세요. "
        "입력에 여러 사건이 섞여 있으면 각각 별도의 후보로 나누세요. "
        "\n\n"

        "Use only categories and statuses that exist in allowed_values. "
        "category와 status는 반드시 allowed_values에 있는 값만 사용하세요. "
        "\n\n"

        "Do not create new categories that are not included in allowed_values. "
        "allowed_values에 없는 category를 새로 만들지 마세요. "
        "\n\n"

        "Classify health issues, unusual conditions, symptoms, injuries, pain, skin problems, appetite changes, energy changes, "
        "breathing problems, coughing, vomiting, diarrhea, bloody stool, seizures, tremors, lumps, tumors, cancer, diagnoses, "
        "suspected diseases, medication, tests, treatment, and vet visits as medical records when the context supports it. "
        "건강 이상, 특이사항, 증상, 상처, 통증, 피부 문제, 식욕 변화, 기력 변화, 호흡 문제, 기침, 구토, 설사, 혈변, "
        "경련, 떨림, 발작, 혹, 멍울, 종양, 암, 진단명, 의심 질환, 약 복용, 검사, 치료, 병원 방문은 "
        "문맥상 건강 관련 기록으로 보고 medical category로 분류하세요. "
        "\n\n"

        "Do not require explicit words such as 'hospital', 'medicine', or 'treatment' to classify something as medical. "
        "사용자가 '병원', '약', '진료'라는 단어를 말하지 않았더라도 건강 이상이나 특이사항으로 보이면 medical 후보로 분리하세요. "
        "\n\n"

        "Examples of medical-context records include: 'a lump is felt on the belly', 'keeps coughing', 'barely ate today', "
        "'seems low energy', 'limping', 'trembled like a seizure', 'scratched the ear until it bled'. "
        "medical 문맥 예시는 다음과 같습니다: '배 쪽에 혹이 만져져', '기침을 계속 했어', '오늘 밥을 거의 안 먹었어', "
        "'기운이 없어 보여', '다리를 절뚝거려', '경련처럼 떨었어', '귀를 긁어서 피가 났어'. "
        "\n\n"

        "Classify observable emotional or behavioral reactions as behavior records. "
        "관찰 가능한 감정 반응이나 행동 반응은 behavior category로 분류하세요. "
        "\n\n"

        "Behavior records may include fear, barking, whining, anxiety, excitement, sensitivity, hiding, unusual reactions, or restlessness. "
        "behavior 기록에는 무서워함, 짖음, 낑낑거림, 불안, 흥분, 예민함, 숨음, 이상 반응, 안절부절못함 등이 포함될 수 있습니다. "
        "\n\n"

        "If a behavior-like expression may indicate a health issue, such as tremors, seizures, collapse, severe lethargy, or repeated vomiting, "
        "consider medical as well. "
        "떨림, 경련, 발작, 쓰러짐, 심한 기력 저하, 반복 구토처럼 행동처럼 보이지만 건강 이상 가능성이 있는 표현은 medical 후보도 고려하세요. "
        "\n\n"

        "Record only observed facts from the user's input. "
        "사용자가 입력한 관찰 사실만 기록하세요. "
        "\n\n"

        "Do not invent events, times, quantities, symptoms, diagnoses, causes, treatments, or medical facts that the user did not mention. "
        "사용자가 말하지 않은 사건, 시간, 수량, 증상, 진단, 원인, 치료, 의학적 사실을 임의로 만들어내지 마세요. "
        "\n\n"

        "Do not make a medical diagnosis. "
        "의학적 진단을 단정하지 마세요. "
        "\n\n"

        "If the user says the pet was diagnosed with cancer, record that the diagnosis was received. "
        "사용자가 '암 진단을 받았다'고 말한 경우에는 '암 진단을 받음'처럼 기록할 수 있습니다. "
        "\n\n"

        "However, if the user only says there is a lump, do not infer cancer. Record it only as a lump or suspected issue. "
        "하지만 사용자가 단순히 혹이나 멍울이 있다고만 말한 경우 암으로 추정하지 말고, 혹 또는 의심되는 이상으로만 기록하세요. "
        "\n\n"

        "Set needs_confirmation=true when confidence is low or guardian confirmation is needed. "
        "확신이 낮거나 보호자 확인이 필요한 내용은 needs_confirmation=true로 설정하세요. "
        "\n\n"

        "Serious symptoms, disease names, diagnoses, unclear quantities, ambiguous expressions, and uncertain interpretations should usually require confirmation. "
        "심각한 증상, 질병명, 진단명, 애매한 수량, 모호한 표현, 불확실한 해석은 보호자 확인이 필요할 수 있습니다. "
        "\n\n"

        "Write each candidate title briefly and clearly. "
        "각 후보의 title은 짧고 명확하게 작성하세요. "
        "\n\n"

        "Write each candidate detail as a concise Korean sentence that preserves the user's meaning. "
        "각 후보의 detail은 사용자의 의미를 보존하는 간결한 한국어 문장으로 작성하세요. "
        "\n\n"

        "Put useful extracted values into measurements, such as time, amount, count, duration, weight, body part, medicine frequency, or location. "
        "measurements에는 시간, 양, 횟수, 기간, 체중, 부위, 약 복용 빈도, 위치처럼 기록에 도움이 되는 값을 넣으세요."
    )


def record_structuring_user_prompt(input: PetLogAgentInput) -> str:
    return (
        "Convert the following input into StructuredRecordBatch format. "
        "다음 입력을 StructuredRecordBatch 형식으로 변환하세요. "
        "\n\n"

        "Use only categories and statuses from allowed_values. "
        "category와 status는 allowed_values에 있는 값만 사용하세요. "
        "\n\n"

        "If multiple record-worthy events are mixed in one sentence, split them into multiple candidates. "
        "하나의 문장에 여러 기록할 만한 사건이 섞여 있으면 candidates를 여러 개로 나누세요. "
        "\n\n"

        "Classify by understanding the full context, not by fixed keywords alone. "
        "고정 키워드만 보지 말고 전체 문맥을 기준으로 분류하세요. "
        "\n\n"
        + json.dumps(
            {
                "input": input_payload(input),
                "allowed_values": allowed_values_payload(),
                "classification_rules": [
                    (
                        "Meal records: food, kibble, wet food, treats, water intake, feeding amount, eaten amount, and leftover amount. "
                        "식사 기록: 사료, 밥, 습식, 건식, 간식, 물 섭취, 급여량, 먹은 양, 남긴 양은 meal로 분류하세요. "
                        "If appetite loss or sudden refusal to eat seems like a health issue, also consider a medical candidate. "
                        "식욕 없음이나 갑작스러운 식사 거부가 건강 이상처럼 보이면 medical 후보도 고려하세요."
                    ),
                    (
                        "Walk records: walking, exercise, walking time, distance, and activities during a walk. "
                        "산책 기록: 산책, 운동, 걸은 시간, 거리, 산책 중 활동은 walk로 분류하세요."
                    ),
                    (
                        "Potty records: urine, feces, potty, normal stool, and routine elimination. "
                        "배변 기록: 소변, 대변, 배변, 일반적인 변 상태, 일상적인 배변은 stool로 분류하세요. "
                        "If stool condition suggests a health issue, such as diarrhea, bloody stool, repeated vomiting, or abnormal color, consider medical as well. "
                        "설사, 혈변, 반복 구토, 비정상적인 색처럼 건강 이상이 의심되는 배변 상태는 medical 후보도 고려하세요."
                    ),
                    (
                        "Medical records: vet visits, medicine, treatment, injections, tests, surgery, wounds, pain, skin issues, lumps, tumors, cancer, coughing, vomiting, diarrhea, seizures, tremors, limping, appetite loss, and low energy. "
                        "병원/건강 기록: 병원, 약, 진료, 검사, 주사, 치료, 처방, 수술, 상처, 통증, 피부 이상, 혹, 종양, 암, 기침, 구토, 설사, 경련, 발작, 절뚝거림, 식욕 없음, 기운 없음 등은 medical로 분류하세요."
                    ),
                    (
                        "Behavior records: fear, barking, whining, anxiety, excitement, sensitivity, hiding, unusual reactions, and emotional responses. "
                        "행동 기록: 무서워함, 짖음, 낑낑거림, 불안, 흥분, 예민함, 숨음, 이상 반응, 감정 반응은 behavior로 분류하세요."
                    ),
                    (
                        "Preserve user-provided disease names or diagnoses, but never infer a diagnosis that the user did not explicitly say. "
                        "사용자가 말한 질병명이나 진단명은 그대로 기록하되, 사용자가 직접 말하지 않은 진단을 추정하지 마세요."
                    ),
                    (
                        "If a phrase is medically serious, ambiguous, or uncertain, set needs_confirmation=true. "
                        "심각하거나 애매하거나 불확실한 표현은 needs_confirmation=true로 설정하세요."
                    ),
                ],
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
                    },
                    {
                        "text": (
                            "꾸꾸 오늘 아침 8시에 사료 30g 먹었고, 8시 반에 산책 1시간 했고, "
                            "산책 중 소변과 대변을 봤어. 집에 와서 손발 닦고 쉬는 중에 머리를 긁어서 "
                            "피가 나서 병원에 가서 진료를 받았어. 진료를 받는데 무서워해서 엄청 짖더라고."
                        ),
                        "candidates": [
                            {
                                "category": "meal",
                                "title": "식사",
                                "detail": "오늘 아침 8시에 사료 30g 먹음",
                                "measurements": ["오늘 아침 8시", "사료 30g"],
                            },
                            {
                                "category": "walk",
                                "title": "산책",
                                "detail": "8시 반에 산책을 1시간 함",
                                "measurements": ["8시 반", "1시간"],
                            },
                            {
                                "category": "stool",
                                "title": "배변",
                                "detail": "산책 중 소변과 대변을 봄",
                                "measurements": ["소변", "대변"],
                            },
                            {
                                "category": "medical",
                                "title": "머리 긁음 및 진료",
                                "detail": "쉬는 중 머리를 긁어서 피가 나 병원에서 진료를 받음",
                                "measurements": ["머리", "피"],
                            },
                            {
                                "category": "behavior",
                                "title": "진료 중 짖음",
                                "detail": "진료를 받는 동안 무서워해서 많이 짖음",
                                "measurements": [],
                            },
                        ],
                    },
                    {
                        "text": (
                            "오늘 콩이가 밥을 거의 안 먹고 기운이 없어 보였어. "
                            "오후에는 기침을 여러 번 했고, 배 쪽에 작은 혹 같은 게 만져졌어."
                        ),
                        "candidates": [
                            {
                                "category": "meal",
                                "title": "식사량 감소",
                                "detail": "오늘 밥을 거의 먹지 않음",
                                "measurements": [],
                            },
                            {
                                "category": "medical",
                                "title": "기운 없음",
                                "detail": "오늘 기운이 없어 보임",
                                "measurements": [],
                            },
                            {
                                "category": "medical",
                                "title": "기침",
                                "detail": "오후에 기침을 여러 번 함",
                                "measurements": ["오후", "여러 번"],
                            },
                            {
                                "category": "medical",
                                "title": "배 쪽 혹",
                                "detail": "배 쪽에 작은 혹 같은 것이 만져짐",
                                "measurements": ["배 쪽", "작은 혹"],
                            },
                        ],
                    },
                    {
                        "text": (
                            "병원에서 검사받았는데 종양 가능성이 있다고 해서 다음 주에 추가 검사를 하기로 했어. "
                            "집에 와서는 계속 불안해하고 낑낑거렸어."
                        ),
                        "candidates": [
                            {
                                "category": "medical",
                                "title": "검사 및 추가 검사 예정",
                                "detail": "병원 검사에서 종양 가능성이 있다고 들었고 다음 주 추가 검사를 하기로 함",
                                "measurements": ["다음 주"],
                            },
                            {
                                "category": "behavior",
                                "title": "불안 반응",
                                "detail": "집에 와서 계속 불안해하고 낑낑거림",
                                "measurements": [],
                            },
                        ],
                    },
                    {
                        "text": (
                            "병원에서 암 진단을 받았고 약을 하루 두 번 먹이라고 했어. "
                            "오늘 저녁 약은 먹였는데 이후에 한 번 토했어."
                        ),
                        "candidates": [
                            {
                                "category": "medical",
                                "title": "암 진단 및 약 복용",
                                "detail": "병원에서 암 진단을 받았고 약을 하루 두 번 먹이라는 안내를 받음",
                                "measurements": ["하루 두 번"],
                            },
                            {
                                "category": "medical",
                                "title": "약 복용 후 구토",
                                "detail": "오늘 저녁 약을 먹인 뒤 한 번 토함",
                                "measurements": ["오늘 저녁", "1번"],
                            },
                        ],
                    },
                ],
            },
            ensure_ascii=False,
        )
    )

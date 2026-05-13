from __future__ import annotations

import json

from domain.models import PetProfile


def build_voice_transcript_correction_messages(pet: PetProfile, text: str) -> list[tuple[str, str]]:
    return [
        ("system", voice_transcript_correction_system_prompt()),
        ("user", voice_transcript_correction_user_prompt(pet, text)),
    ]


def voice_transcript_correction_system_prompt() -> str:
    return (
        "You are an expert AI assistant that corrects Korean speech-to-text (STT) misrecognitions "
        "for a pet care logging application. "
        "당신은 반려동물 케어 기록 애플리케이션에서 한국어 음성 인식(STT) 오류를 교정하는 전문 AI 어시스턴트입니다. "
        "\n\n"
        "Your task is not simple typo replacement. Your task is contextual reconstruction. "
        "First, understand the full care-log situation as a human guardian would understand it. "
        "Then identify unnatural, semantically broken, or phonetically suspicious spans in the recognized text. "
        "당신의 역할은 단순 오타 치환이 아닙니다. 문맥 기반 복원입니다. "
        "먼저 보호자가 말한 전체 케어 기록 상황을 사람처럼 이해하세요. "
        "그 다음 인식 문장에서 부자연스럽거나, 의미가 깨졌거나, 발음상 의심스러운 구간을 찾으세요. "
        "\n\n"
        "Use a two-pass correction process. "
        "Pass 1: silently infer the most natural corrected full sentence while preserving the user's meaning. "
        "Pass 2: compare the original recognized text with that corrected sentence and return only the changed spans as suggestions. "
        "2단계 교정 과정을 사용하세요. "
        "1단계: 사용자의 의미를 보존하면서 가장 자연스러운 전체 교정 문장을 내부적으로 먼저 추론하세요. "
        "2단계: 원래 recognized_text와 내부적으로 추론한 교정 문장을 비교해서, 바뀐 구간만 suggestions로 반환하세요. "
        "\n\n"
        "Return every likely correction after scanning the entire recognized text from beginning to end. "
        "Do not stop after finding only one correction. "
        "인식된 문장 전체를 처음부터 끝까지 확인한 뒤 가능한 모든 교정 후보를 반환하세요. "
        "오류 하나를 찾았다고 멈추면 안 됩니다. "
        "\n\n"
        "Do not limit corrections to a single word. If several consecutive words are clearly corrupted by STT, "
        "you may suggest replacing the full corrupted phrase with one natural pet-care phrase. "
        "단어 하나만 고치려고 하지 마세요. 여러 단어가 연속으로 잘못 인식되어 문맥이 깨졌다면, "
        "그 전체 구간을 하나의 자연스러운 반려동물 케어 표현으로 교정 제안할 수 있습니다. "
        "\n\n"
        "Actively detect broken Korean phrases. A phrase can be suspicious even if every individual word exists. "
        "In pet care logs, unnatural combinations should be checked against the surrounding event sequence. "
        "깨진 한국어 표현을 적극적으로 탐지하세요. 개별 단어가 실제로 존재하더라도 구절 전체가 부자연스러우면 의심해야 합니다. "
        "반려동물 기록에서는 주변 사건 흐름과 맞지 않는 조합을 문맥으로 확인해야 합니다. "
        "\n\n"
        "Use the pet care context actively when the recognized text is unnatural. "
        "Common pet-care contexts include feeding, water intake, walking, potty, urine, feces, wiping paws, resting, "
        "scratching, bleeding, grooming, bathing, vet visits, treatment, fear, barking, trembling, whining, pain, and symptoms. "
        "인식 결과가 부자연스러우면 반려동물 케어 문맥을 적극적으로 활용하세요. "
        "대표적인 반려동물 케어 문맥에는 급여, 음수, 산책, 배변, 소변, 대변, 손발 닦기, 휴식, "
        "긁기, 피가 남, 미용, 목욕, 병원 방문, 진료, 치료, 무서워함, 짖음, 떨림, 낑낑거림, 통증, 증상이 포함됩니다. "
        "\n\n"
        "In walking and potty contexts, if the sentence says the pet was on a walk and then contains a malformed phrase "
        "near words like feces, potty, or 'saw/did potty', consider whether the intended meaning is urine and feces together. "
        "Do not require an exact memorized error pattern. Use semantic fit, Korean naturalness, and phonetic similarity together. "
        "산책과 배변 문맥에서, 산책 중이었다는 내용 뒤에 대변, 배변, 봤어 같은 단어 근처에 깨진 표현이 나오면 "
        "소변과 대변을 함께 봤다는 의미인지 검토하세요. "
        "정확히 외운 오류 패턴이 아니어도 됩니다. 의미 적합성, 한국어 자연스러움, 발음 유사성을 함께 사용하세요. "
        "\n\n"
        "Prefer natural pet-care expressions over unrelated everyday words when the surrounding context clearly supports it. "
        "앞뒤 문맥이 명확하다면 관련 없는 일반 단어보다 자연스러운 반려동물 케어 표현을 우선하세요. "
        "\n\n"
        "When a phrase is suspicious but not certain, still return it as a correction suggestion if the user can safely confirm it. "
        "The UI will ask the guardian whether to apply the correction, so suggestions may include plausible context-based corrections. "
        "어떤 표현이 의심스럽지만 100% 확실하지 않아도, 보호자가 확인할 수 있는 수준의 합리적인 교정이면 제안하세요. "
        "UI에서 보호자에게 적용 여부를 묻기 때문에, 문맥상 가능성이 높은 교정은 suggestions에 포함할 수 있습니다. "
        "\n\n"
        "Very important preservation rules: do not rewrite the user's speaking style, honorific level, spacing style, or number notation "
        "unless that exact part is the STT error span. "
        "매우 중요한 보존 규칙: 오류 구간이 아닌 부분의 말투, 존댓말/반말, 띄어쓰기 스타일, 숫자 표기는 바꾸지 마세요. "
        "\n\n"
        "Do not change casual endings such as '했어', '봤어', '받았어', '더라고' into polite endings like '했어요', '봤어요'. "
        "'했어', '봤어', '받았어', '더라고' 같은 반말 어미를 '했어요', '봤어요' 같은 존댓말로 바꾸지 마세요. "
        "\n\n"
        "Do not convert numeric expressions unless the number or unit itself is wrong. "
        "For example, keep '1시간' as '1시간'. Do not rewrite it as '한 시간'. "
        "숫자 또는 단위 자체가 틀린 경우가 아니면 숫자 표현을 바꾸지 마세요. "
        "예를 들어 '1시간'은 그대로 '1시간'으로 유지하고 '한 시간'으로 바꾸지 마세요. "
        "\n\n"
        "High-priority pet-care STT correction patterns are examples, not the full list. "
        "'서류' in a feeding context is likely '사료'; "
        "'선발 닦고' after coming home from a walk is likely '손발 닦고'; "
        "'병원에 가서 공부를 받았어' is likely '병원에 가서 진료를 받았어'; "
        "'무서워해서 엄청 춥더라고' in a vet-visit context is likely '무서워해서 엄청 짖더라고'. "
        "우선순위가 높은 반려동물 STT 교정 패턴은 예시일 뿐 전체 목록이 아닙니다. "
        "급여 문맥의 '서류'는 '사료'일 가능성이 높습니다. "
        "산책 후 집에 온 문맥의 '선발 닦고'는 '손발 닦고'일 가능성이 높습니다. "
        "병원 문맥의 '병원에 가서 공부를 받았어'는 '병원에 가서 진료를 받았어'일 가능성이 높습니다. "
        "병원에서 무서워했다는 문맥의 '무서워해서 엄청 춥더라고'는 '무서워해서 엄청 짖더라고'일 가능성이 높습니다. "
        "\n\n"
        "Do NOT invent new events, times, quantities, symptoms, medical facts, or behaviors that are not supported by the text. "
        "원문에서 근거를 찾을 수 없는 새로운 사건, 시간, 수량, 증상, 의학적 사실, 행동을 임의로 만들어내면 안 됩니다. "
        "\n\n"
        "However, if the recognized phrase is clearly unnatural and a phonetically similar pet-care phrase fits the context, "
        "you should suggest the correction. "
        "다만 인식된 표현이 명확히 부자연스럽고, 발음이 비슷한 반려동물 케어 표현이 문맥에 맞는다면 교정 제안을 하세요. "
        "\n\n"
        "Each suggestion must replace only one specific error span. "
        "각 suggestion은 하나의 특정 오류 구간만 교체해야 합니다. "
        "\n\n"
        "For each suggestion, 'from_text' must be an exact substring of recognized_text. "
        "각 suggestion의 'from_text'는 반드시 recognized_text 안에 실제로 존재하는 정확한 문자열이어야 합니다. "
        "\n\n"
        "For each suggestion, 'suggested_text' must contain the full original recognized_text with ONLY that suggestion's from_text replaced by to_text. "
        "각 suggestion의 'suggested_text'에는 전체 recognized_text를 넣되, 반드시 해당 suggestion의 from_text만 to_text로 교체해야 합니다. "
        "\n\n"
        "You must return the suggestions in the strictly requested JSON format. "
        "반드시 요청된 JSON 형식을 엄격하게 지켜 응답해야 합니다. "
        "\n\n"
        "Write the 'reason' field in natural Korean for the end-user. "
        "'reason' 필드는 최종 사용자가 이해하기 쉬운 자연스러운 한국어로 작성하세요."
    )


def voice_transcript_correction_user_prompt(pet: PetProfile, text: str) -> str:
    return json.dumps(
        {
            "pet_profile": {
                "name": pet.name,
                "breed": pet.breed,
                "species": pet.species,
                "age_label": pet.age_label,
                "personality": pet.personality,
                "notes": list(pet.notes),
            },
            "recognized_text": text.strip(),
            "pet_care_terms": [
                "사료",
                "간식",
                "물",
                "음수",
                "급여",
                "산책",
                "소변",
                "대변",
                "배변",
                "손발 닦기",
                "발 닦기",
                "쉬는 중",
                "휴식",
                "긁다",
                "핥다",
                "피가 나다",
                "상처",
                "피부",
                "귀",
                "눈",
                "머리",
                "몸",
                "목욕",
                "미용",
                "병원",
                "동물병원",
                "진료",
                "치료",
                "검진",
                "처방",
                "주사",
                "약",
                "무서워하다",
                "짖다",
                "떨다",
                "낑낑거리다",
                "토하다",
                "설사",
                "기침",
            ],
            "semantic_correction_strategy": [
                (
                    "First infer the full intended care log from context, then return only the changed spans as suggestions. "
                    "먼저 문맥상 의도된 전체 케어 기록을 추론한 뒤, 실제로 바뀐 구간만 suggestions로 반환하세요."
                ),
                (
                    "Do not depend only on memorized wrong-to-correct pairs. "
                    "Look for broken Korean, odd noun combinations, and phrases that do not fit the surrounding care event. "
                    "외운 오인식 쌍에만 의존하지 마세요. "
                    "깨진 한국어, 어색한 명사 조합, 주변 케어 사건과 맞지 않는 표현을 찾으세요."
                ),
                (
                    "For walking and potty records, check whether strange text near feces/potty expressions should be restored "
                    "as a natural urine-and-feces phrase. "
                    "산책과 배변 기록에서는 대변/배변 표현 주변의 이상한 텍스트가 "
                    "소변과 대변을 함께 봤다는 자연스러운 표현으로 복원되어야 하는지 확인하세요."
                ),
                (
                    "When the surrounding context is strong, a plausible correction can be returned as a suggestion even if it is not certain. "
                    "The guardian will decide whether to apply it. "
                    "주변 문맥이 강하면 100% 확실하지 않아도 합리적인 교정 후보를 제안할 수 있습니다. "
                    "최종 적용 여부는 보호자가 결정합니다."
                ),
            ],
            "high_priority_correction_patterns": [
                {
                    "wrong": "서류",
                    "correct": "사료",
                    "context": "먹었다, g, 급여량, 아침/저녁 식사 같은 급여 문맥",
                },
                {
                    "wrong": "선발 닦고",
                    "correct": "손발 닦고",
                    "context": "산책 후 집에 와서 닦는 행동 문맥",
                },
                {
                    "wrong": "공부를 받았어",
                    "correct": "진료를 받았어",
                    "context": "병원에 가서 무엇을 받았다는 문맥",
                },
                {
                    "wrong": "공부를 받았어요",
                    "correct": "진료를 받았어요",
                    "context": "병원에 가서 무엇을 받았다는 문맥",
                },
                {
                    "wrong": "춥더라고",
                    "correct": "짖더라고",
                    "context": "병원, 진료, 무서워함, 반려견 반응 문맥",
                },
                {
                    "wrong": "춥더라",
                    "correct": "짖더라",
                    "context": "병원, 진료, 무서워함, 반려견 반응 문맥",
                },
            ],
            "preservation_rules": [
                "오류가 아닌 부분은 절대 문체를 바꾸지 마세요.",
                "반말을 존댓말로 바꾸지 마세요. 예: '봤어'를 '봤어요'로 바꾸지 마세요.",
                "존댓말을 반말로 바꾸지 마세요.",
                "숫자 표기를 임의로 바꾸지 마세요. 예: '1시간'을 '한 시간'으로 바꾸지 마세요.",
                "오류가 아닌 조사, 어미, 띄어쓰기, 구두점을 불필요하게 바꾸지 마세요.",
                "suggested_text는 전체 문장을 다시 쓰는 곳이 아니라, from_text 하나만 to_text로 바꾼 결과를 보여주는 곳입니다.",
            ],
            "guidelines": [
                (
                    "1. Analyze the entire recognized_text from beginning to end. "
                    "Do not stop after finding one correction. "
                    "recognized_text 전체를 처음부터 끝까지 분석하세요. 오류 하나를 찾았다고 멈추지 마세요."
                ),
                (
                    "2. Before creating suggestions, internally reconstruct the most natural full sentence. "
                    "Then extract only the changed spans into suggestions. "
                    "suggestions를 만들기 전에 가장 자연스러운 전체 문장을 내부적으로 먼저 복원하세요. "
                    "그 다음 바뀐 구간만 suggestions로 추출하세요."
                ),
                (
                    "3. Look for semantic dissonance where a recognized word or phrase does not fit the pet-care situation. "
                    "인식된 단어 또는 구절이 반려동물 케어 상황에 맞지 않는 의미상 불일치를 찾으세요."
                ),
                (
                    "4. Look for broken Korean phrases, unnatural noun sequences, and phrases that sound like STT artifacts. "
                    "They may need phrase-level correction even if no exact example exists. "
                    "깨진 한국어 표현, 부자연스러운 명사 나열, 음성 인식 오류처럼 보이는 구절을 찾으세요. "
                    "정확히 같은 예시가 없어도 구절 단위 교정이 필요할 수 있습니다."
                ),
                (
                    "5. If an awkward word or phrase sounds phonetically similar to a natural pet-care term, suggest a correction. "
                    "어색한 단어 또는 구절이 자연스러운 반려동물 케어 용어와 발음이 비슷하다면 교정을 제안하세요."
                ),
                (
                    "6. Do not limit corrections to one word. If multiple consecutive words are corrupted, "
                    "suggest a phrase-level correction. "
                    "단어 하나만 수정하려고 하지 마세요. 여러 단어가 연속으로 잘못 인식되었다면 구절 단위로 교정하세요."
                ),
                (
                    "7. Correct pet name misrecognitions. If a word sounds like the pet's name or is an out-of-place proper noun "
                    "in the subject position, correct it. "
                    "반려동물 이름 오인식을 교정하세요. 주어 위치에 반려동물 이름처럼 들리거나 문맥상 어색한 고유명사가 있다면 교정하세요."
                ),
                (
                    "8. Fix incorrect food-related words, units, or particles based on context. "
                    "For example, in a feeding context, '서류' may be '사료', and '30분은 먹었고' may be '30g 먹었고'. "
                    "급여 문맥에서는 음식 관련 단어, 단위, 조사를 문맥에 맞게 교정하세요. "
                    "예를 들어 '서류'는 '사료', '30분은 먹었고'는 '30g 먹었고'일 수 있습니다."
                ),
                (
                    "9. Fix incorrect walking or duration expressions based on context, but preserve numeric notation if it is already correct. "
                    "For example, '산책할 시간 있고' may be '산책 1시간 했고', but '산책 1시간 했고' must remain '산책 1시간 했고'. "
                    "산책 문맥에서는 산책 여부와 시간 표현을 문맥에 맞게 교정하되, 이미 맞는 숫자 표기는 유지하세요. "
                    "예를 들어 '산책할 시간 있고'는 '산책 1시간 했고'일 수 있지만, '산책 1시간 했고'를 '산책 한 시간 했고'로 바꾸면 안 됩니다."
                ),
                (
                    "10. In a walking or potty context, if an odd phrase appears right before or around words like '대변', '배변', or '봤어', "
                    "check whether the intended phrase is a natural urine-and-feces expression. "
                    "Do not require the exact wrong phrase to be listed in examples. "
                    "산책 또는 배변 문맥에서 '대변', '배변', '봤어' 같은 단어 바로 앞이나 주변에 이상한 표현이 나오면 "
                    "소변과 대변을 함께 봤다는 자연스러운 표현인지 확인하세요. "
                    "잘못 인식된 표현이 예시와 정확히 같을 필요는 없습니다."
                ),
                (
                    "11. Fix awkward post-walk care phrases. "
                    "After a walk, phrases like wiping paws, resting, scratching, and bleeding are common. "
                    "산책 후 관리 문맥을 교정하세요. 산책 후에는 손발 닦기, 쉬는 중, 긁기, 피가 남 같은 표현이 자연스럽습니다."
                ),
                (
                    "12. Fix awkward noun combinations. "
                    "For example, during a walk, an absurd or broken phrase near feces/potty expressions can be corrected "
                    "to a natural urine-and-feces phrase when supported by context. "
                    "'선발 닦고' should be '손발 닦고'. "
                    "어색한 명사 조합을 교정하세요. 예를 들어 산책 문맥에서 대변/배변 표현 주변의 깨진 구절은 "
                    "문맥상 자연스러운 소변과 대변 표현으로 교정될 수 있습니다. "
                    "'선발 닦고'는 '손발 닦고'가 자연스럽습니다."
                ),
                (
                    "13. Fix awkward verbs based on cause-and-effect. "
                    "For example, '머리를 감아서 피가 나서' is awkward because washing does not normally cause bleeding, "
                    "but '긁어서' can cause bleeding and sounds similar. "
                    "원인과 결과 관계를 기준으로 어색한 동사를 교정하세요. 예를 들어 '머리를 감아서 피가 나서'는 어색하며, "
                    "상처가 날 수 있는 행동인 '긁어서'의 오인식일 수 있습니다."
                ),
                (
                    "14. Fix vet-visit action expressions. "
                    "In a hospital or vet-visit context, phrases like '공부를 받았어' or '공부를 받았어요' are unnatural; "
                    "they are likely '진료를 받았어' or '진료를 받았어요'. "
                    "병원 또는 동물병원 문맥에서 '공부를 받았어', '공부를 받았어요'는 부자연스럽습니다. "
                    "이 경우 '진료를 받았어', '진료를 받았어요'가 자연스럽습니다."
                ),
                (
                    "15. Fix fear or reaction expressions in vet-visit contexts. "
                    "If the text says the pet was scared at the vet, reactions like barking, trembling, or whining are more natural "
                    "than unrelated states like being cold. "
                    "병원 방문 문맥에서 무서워했다는 내용이 나오면, 춥다는 표현보다 짖음, 떨림, 낑낑거림 같은 반응이 자연스럽습니다."
                ),
                (
                    "16. Prefer common pet-care phrases over unrelated everyday words when the sentence is about feeding, walking, "
                    "potty, grooming, injury, vet visits, fear, or barking. "
                    "급여, 산책, 배변, 관리, 상처, 병원 방문, 무서워함, 짖음 문맥에서는 관련 없는 일반 단어보다 "
                    "반려동물 케어 표현을 우선하세요."
                ),
                (
                    "17. Preserve the user's original speaking style and endings. "
                    "Do not change '봤어' to '봤어요', '받았어' to '받았어요', or '했어' to '했습니다'. "
                    "사용자의 원래 말투와 어미를 유지하세요. "
                    "'봤어'를 '봤어요'로, '받았어'를 '받았어요'로, '했어'를 '했습니다'로 바꾸지 마세요."
                ),
                (
                    "18. Preserve number notation when the recognized number is already correct. "
                    "Do not change '1시간' to '한 시간', '30g' to '삼십 그램', or '8시 반' to '8시 30분' unless the original is clearly wrong. "
                    "인식된 숫자 표현이 이미 맞다면 그대로 유지하세요. "
                    "'1시간'을 '한 시간'으로, '30g'을 '삼십 그램'으로, '8시 반'을 '8시 30분'으로 바꾸지 마세요."
                ),
                (
                    "19. Only suggest a correction when the original recognized phrase is unnatural, contextually suspicious, "
                    "or likely to be an STT artifact, and the correction is supported by semantic fit, phonetic similarity, or strong pet-care context. "
                    "원래 인식된 표현이 부자연스럽거나, 문맥상 의심스럽거나, 음성 인식 오류처럼 보이고, "
                    "의미 적합성, 발음 유사성, 강한 반려동물 케어 문맥 중 하나 이상으로 교정이 뒷받침될 때 제안하세요."
                ),
                (
                    "20. Do not invent new events, times, quantities, symptoms, or medical facts. "
                    "새로운 사건, 시간, 수량, 증상, 의학적 사실을 임의로 만들지 마세요."
                ),
                (
                    "21. Return every likely correction as a separate item in suggestions. "
                    "가능성이 높은 모든 교정 후보를 suggestions 배열에 각각 별도 항목으로 반환하세요."
                ),
                (
                    "22. 'from_text' MUST be an exact substring of recognized_text. "
                    "'from_text'는 반드시 recognized_text 안에 실제로 존재하는 정확한 문자열이어야 합니다."
                ),
                (
                    "23. 'suggested_text' MUST contain the full original recognized_text with ONLY the specific 'from_text' replaced by 'to_text'. "
                    "'suggested_text'에는 전체 recognized_text를 넣되, 반드시 해당 항목의 'from_text'만 'to_text'로 교체해야 합니다."
                ),
                (
                    "24. The 'reason' field MUST be written in natural Korean. "
                    "'reason' 필드는 반드시 자연스러운 한국어로 작성해야 합니다."
                ),
            ],
            "response_format": {
                "suggestions": [
                    {
                        "from_text": "원문에서 교정이 필요한 특정 단어 또는 구절",
                        "to_text": "교정된 단어 또는 구절",
                        "reason": "왜 이렇게 교정하는지에 대한 자연스러운 한국어 설명",
                        "suggested_text": "전체 recognized_text에서 해당 from_text만 to_text로 바꾼 문장",
                    }
                ]
            },
            "examples": [
                {
                    "recognized_text": (
                        "꾸꾸 오늘 아침 8시에 서류 30g 먹었고 8시 반에 산책 1시간 했고 "
                        "산책 중에 소변과 대변을 봤어 집에 와서 선발 닦고 쉬는 중에 머리를 긁어서 "
                        "피가 나서 병원에 가서 공부를 받았어 진료를 받는데 무서워해서 엄청 춥더라고"
                    ),
                    "suggestions": [
                        {
                            "from_text": "서류",
                            "to_text": "사료",
                            "reason": (
                                "아침에 30g을 먹었다는 급여 문맥에서 '서류'는 어색하며, "
                                "반려동물이 먹는 것은 '사료'가 자연스럽습니다."
                            ),
                            "suggested_text": (
                                "꾸꾸 오늘 아침 8시에 사료 30g 먹었고 8시 반에 산책 1시간 했고 "
                                "산책 중에 소변과 대변을 봤어 집에 와서 선발 닦고 쉬는 중에 머리를 긁어서 "
                                "피가 나서 병원에 가서 공부를 받았어 진료를 받는데 무서워해서 엄청 춥더라고"
                            ),
                        },
                        {
                            "from_text": "선발 닦고",
                            "to_text": "손발 닦고",
                            "reason": (
                                "산책 후 집에 와서 닦는 문맥에서는 '선발 닦고'보다 "
                                "'손발 닦고'가 자연스럽습니다."
                            ),
                            "suggested_text": (
                                "꾸꾸 오늘 아침 8시에 서류 30g 먹었고 8시 반에 산책 1시간 했고 "
                                "산책 중에 소변과 대변을 봤어 집에 와서 손발 닦고 쉬는 중에 머리를 긁어서 "
                                "피가 나서 병원에 가서 공부를 받았어 진료를 받는데 무서워해서 엄청 춥더라고"
                            ),
                        },
                        {
                            "from_text": "공부를 받았어",
                            "to_text": "진료를 받았어",
                            "reason": (
                                "병원에 가서 무엇을 받았다는 문맥에서는 '공부를 받았어'보다 "
                                "'진료를 받았어'가 자연스럽습니다."
                            ),
                            "suggested_text": (
                                "꾸꾸 오늘 아침 8시에 서류 30g 먹었고 8시 반에 산책 1시간 했고 "
                                "산책 중에 소변과 대변을 봤어 집에 와서 선발 닦고 쉬는 중에 머리를 긁어서 "
                                "피가 나서 병원에 가서 진료를 받았어 진료를 받는데 무서워해서 엄청 춥더라고"
                            ),
                        },
                        {
                            "from_text": "춥더라고",
                            "to_text": "짖더라고",
                            "reason": (
                                "진료를 받는데 무서워했다는 문맥에서는 '춥더라고'보다 "
                                "반려견의 반응인 '짖더라고'가 자연스럽습니다."
                            ),
                            "suggested_text": (
                                "꾸꾸 오늘 아침 8시에 서류 30g 먹었고 8시 반에 산책 1시간 했고 "
                                "산책 중에 소변과 대변을 봤어 집에 와서 선발 닦고 쉬는 중에 머리를 긁어서 "
                                "피가 나서 병원에 가서 공부를 받았어 진료를 받는데 무서워해서 엄청 짖더라고"
                            ),
                        },
                    ],
                },
                {
                    "recognized_text": (
                        "꾸꾸 오늘 아침 8시에 사료 30분만 먹었고 8시 반에 산책 한 시간 했고 "
                        "산책 중 의미가 어색한 말과 대변을 봤어 집에 와서 선발 닦고 쉬는 중에 머리를 감아서 "
                        "피가 나서 병원에 가서 진료를 받았어 진료를 받는데 무서워해서 엄청 짖더라고"
                    ),
                    "suggestions": [
                        {
                            "from_text": "30분만",
                            "to_text": "30g",
                            "reason": (
                                "사료를 먹었다는 문맥에서 '30분만'보다는 무게 단위인 '30g'이 적절하며 "
                                "발음이 비슷해 오인식된 것으로 보입니다."
                            ),
                            "suggested_text": (
                                "꾸꾸 오늘 아침 8시에 사료 30g 먹었고 8시 반에 산책 한 시간 했고 "
                                "산책 중 의미가 어색한 말과 대변을 봤어 집에 와서 선발 닦고 쉬는 중에 머리를 감아서 "
                                "피가 나서 병원에 가서 진료를 받았어 진료를 받는데 무서워해서 엄청 짖더라고"
                            ),
                        },
                        {
                            "from_text": "의미가 어색한 말과 대변을",
                            "to_text": "소변과 대변을",
                            "reason": (
                                "산책 중 배변 활동을 말하는 문맥에서 대변 앞의 표현이 부자연스럽습니다. "
                                "소변과 대변을 함께 봤다는 표현이 더 자연스러운 교정 후보입니다."
                            ),
                            "suggested_text": (
                                "꾸꾸 오늘 아침 8시에 사료 30분만 먹었고 8시 반에 산책 한 시간 했고 "
                                "산책 중 소변과 대변을 봤어 집에 와서 선발 닦고 쉬는 중에 머리를 감아서 "
                                "피가 나서 병원에 가서 진료를 받았어 진료를 받는데 무서워해서 엄청 짖더라고"
                            ),
                        },
                        {
                            "from_text": "선발 닦고",
                            "to_text": "손발 닦고",
                            "reason": "집에 와서 닦는 문맥이므로 '선발 닦고'보다는 '손발 닦고'가 알맞습니다.",
                            "suggested_text": (
                                "꾸꾸 오늘 아침 8시에 사료 30분만 먹었고 8시 반에 산책 한 시간 했고 "
                                "산책 중 의미가 어색한 말과 대변을 봤어 집에 와서 손발 닦고 쉬는 중에 머리를 감아서 "
                                "피가 나서 병원에 가서 진료를 받았어 진료를 받는데 무서워해서 엄청 짖더라고"
                            ),
                        },
                        {
                            "from_text": "감아서",
                            "to_text": "긁어서",
                            "reason": (
                                "머리를 감아서 피가 났다는 것은 어색합니다. "
                                "상처가 날 수 있는 행동인 '긁어서'의 오인식으로 보입니다."
                            ),
                            "suggested_text": (
                                "꾸꾸 오늘 아침 8시에 사료 30분만 먹었고 8시 반에 산책 한 시간 했고 "
                                "산책 중 의미가 어색한 말과 대변을 봤어 집에 와서 선발 닦고 쉬는 중에 머리를 긁어서 "
                                "피가 나서 병원에 가서 진료를 받았어 진료를 받는데 무서워해서 엄청 짖더라고"
                            ),
                        },
                    ],
                },
                {
                    "recognized_text": (
                        "꾸꾸 오늘 아침 8시에 사료 30g 먹었고 8시 반에 산책 1시간 했고 "
                        "산책 중에 소변과 대변을 봤어"
                    ),
                    "suggestions": [],
                    "reason": (
                        "이미 자연스러운 문장이므로 '1시간'을 '한 시간'으로 바꾸거나 "
                        "'봤어'를 '봤어요'로 바꾸면 안 됩니다."
                    ),
                },
            ],
        },
        ensure_ascii=False,
    )
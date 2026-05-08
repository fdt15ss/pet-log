from __future__ import annotations

import os
from pathlib import Path

from application.dto import PetLogAgentInput
from domain.models import PetProfile
from infrastructure.llm.record_structuring import RecordStructurer


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    load_env_file(backend_root / ".env")

    batch = RecordStructurer().structure(
        PetLogAgentInput(
            pet=PetProfile(
                id="sample-pet-choco",
                name="초코",
                breed="말티푸",
                species="companion",
                age_label="3살",
                personality="처음엔 낯을 가리지만 저녁 산책을 좋아해요",
                notes=("아침 식사는 천천히 먹는 편", "알러지 의심 간식은 피하기"),
            ),
            text="오늘 오전 8시에 초코가 사료 40g 중 15g만 먹고, 저녁 산책은 12분만 했고, 오른쪽 귀를 5번 긁었어.",
            source="manual",
        )
    )

    print("needs_confirmation:", batch.needs_confirmation)
    for index, candidate in enumerate(batch.candidates, start=1):
        print(f"candidate {index}:", candidate)


if __name__ == "__main__":
    main()

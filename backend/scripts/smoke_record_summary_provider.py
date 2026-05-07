from __future__ import annotations

import os
from pathlib import Path

from domain.models import ContextAnalysisResult, PetProfile, PetRecord, PlannedReminder
from infrastructure.llm.record_summary_provider import RecordSummaryProvider


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

    pet = PetProfile(
        id="pet-1",
        name="초코",
        species="companion",
        personality="겁이 조금 많고 현관 소리에 민감함",
    )
    records = (
        PetRecord(
            id="record-1",
            pet_id="pet-1",
            category="behavior",
            title="밤에 짖음",
            detail="새벽에 현관 쪽을 보고 10분 정도 짖었다.",
            status="notice",
            recorded_at="2026-05-07T01:10:00+09:00",
            source="manual",
        ),
        PetRecord(
            id="record-2",
            pet_id="pet-1",
            category="walk",
            title="저녁 산책 짧게 함",
            detail="비가 와서 평소보다 짧게 12분 정도만 산책했다.",
            status="normal",
            recorded_at="2026-05-06T20:00:00+09:00",
            source="manual",
        ),
    )
    due_items = (
        PlannedReminder(
            title="저녁 산책",
            due_date="2026-05-07",
            reason="평소 루틴 유지",
        ),
    )

    result = RecordSummaryProvider().summarize(
        pet=pet,
        records=records,
        context=ContextAnalysisResult(),
        due_items=due_items,
    )

    print("summary:", result.summary)
    print("record_ids:", result.record_ids)
    print("highlights:", result.highlights)
    print("behavior_patterns:", result.behavior_patterns)
    print("missing_record_notes:", result.missing_record_notes)
    print("safety_notice:", result.safety_notice)


if __name__ == "__main__":
    main()

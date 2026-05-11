from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from application.agents.care_context import CareContextBuilder
from domain.models import CareContext
from infrastructure.database import connect
from infrastructure.llm.care_answer.provider import CareAnswerProvider
from infrastructure.repositories import PetProfileRepository, RecordRepository, ScheduleRepository
from infrastructure.seed_data import SAMPLE_PET_ID, seed_default_data


@dataclass(frozen=True)
class CareQuestionSmokeFixture:
    provider: CareAnswerProvider
    context_builder: CareContextBuilder
    pet_id: str

    def build_context(self) -> CareContext:
        return self.context_builder.build(self.pet_id, lookback_days=30)

    def ask(self, context: CareContext, question: str) -> str:
        return self.provider.answer(context, question)


def build_care_question_smoke_fixture(
    database_path: str | None = ":memory:",
    *,
    seed_today: date = date(2026, 5, 8),
    pet_id: str = SAMPLE_PET_ID,
) -> CareQuestionSmokeFixture:
    connection = connect(database_path)
    # Note: connection is not closed here because we return the fixture which might need it,
    # but since this is an in-memory DB used synchronously, we seed it immediately.
    # In a real app, connection management would be better handled.
    seed_default_data(connection, today=seed_today)
    
    pet_repository = PetProfileRepository(connection=connection)
    record_repository = RecordRepository(connection=connection)
    schedule_repository = ScheduleRepository(connection=connection)
    
    context_builder = CareContextBuilder(
        pet_profile_reader=pet_repository,
        record_history_reader=record_repository,
        schedule_context_reader=schedule_repository,
        days_ahead=14,
    )

    return CareQuestionSmokeFixture(
        provider=CareAnswerProvider(),
        context_builder=context_builder,
        pet_id=pet_id,
    )


def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    load_dotenv(backend_root / ".env", override=False)

    fixture = build_care_question_smoke_fixture()
    context = fixture.build_context()
    
    # Check if user provided a question via CLI
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "요즘 우리 강아지가 사료를 잘 먹고 있나요?"

    print(f"--- Pet Info ---")
    print(f"이름: {context.pet.name}")
    print(f"성격: {context.pet.personality}")
    
    print(f"\n--- Recent Records ({len(context.recent_records)}건) ---")
    for record in context.recent_records:
        print(f"[{record.recorded_at}] {record.title}: {record.detail}")
        
    print(f"\n--- Question ---")
    print(question)

    print(f"\n--- AI Answering... ---")
    answer = fixture.ask(context, question)
    
    print(f"\n--- Answer Result ---")
    # Safe print for Windows console
    safe_answer = answer.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
    print(safe_answer)


if __name__ == "__main__":
    main()

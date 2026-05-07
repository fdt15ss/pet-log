from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

SAMPLE_PET_ID = "sample-pet-choco"
SAMPLE_PET_IDS = ("sample-pet-choco", "sample-pet-nabi", "sample-pet-ddang")


def seed_database(database_path: str | Path | None = None, today: date | None = None) -> None:
    from infrastructure.database import connect

    connection = connect(database_path)
    try:
        seed_default_data(connection, today=today)
    finally:
        connection.close()


def seed_default_data(connection: sqlite3.Connection, today: date | None = None) -> None:
    base_date = today or date.today()
    connection.executemany(
        """
        INSERT OR IGNORE INTO pets (id, name, breed, species, age_label, personality, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                "sample-pet-choco",
                "초코",
                "말티푸",
                "dog",
                "3살",
                "처음엔 낯을 가리지만 저녁 산책을 좋아해요",
                json.dumps(["아침 식사는 천천히 먹는 편", "알러지 의심 간식은 피하기"], ensure_ascii=False),
            ),
            (
                "sample-pet-nabi",
                "나비",
                "코리안숏헤어",
                "cat",
                "5살",
                "조용한 공간을 좋아하고 낯선 사람에게는 신중해요",
                json.dumps(["물그릇 위치가 바뀌면 잘 안 마심", "습식 간식을 좋아함"], ensure_ascii=False),
            ),
            (
                "sample-pet-ddang",
                "땅콩",
                "포메라니안",
                "dog",
                "1살",
                "호기심이 많고 장난감 공을 특히 좋아해요",
                json.dumps(["흥분하면 짖음이 늘어남", "짧은 산책을 여러 번 하는 편"], ensure_ascii=False),
            ),
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO pet_records (id, pet_id, category, title, detail, status, recorded_at, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                "sample-record-meal",
                "sample-pet-choco",
                "meal",
                "아침 식사",
                "사료를 평소보다 조금 더 남겼어요.",
                "notice",
                _at(base_date, time(8, 10)),
                "manual",
            ),
            (
                "sample-record-walk",
                "sample-pet-choco",
                "walk",
                "저녁 산책",
                "공원에서 25분 정도 걸었고 컨디션은 좋아 보였어요.",
                "normal",
                _at(base_date - timedelta(days=1), time(19, 20)),
                "manual",
            ),
            (
                "sample-record-stool",
                "sample-pet-choco",
                "stool",
                "배변 상태",
                "변이 평소보다 조금 무른 편이라 내일까지 지켜보기로 했어요.",
                "notice",
                _at(base_date - timedelta(days=2), time(9, 0)),
                "manual",
            ),
            (
                "sample-record-medical",
                "sample-pet-choco",
                "medical",
                "귀 상태 확인",
                "오른쪽 귀를 자주 긁어서 붉은기가 있는지 확인했어요.",
                "notice",
                _at(base_date - timedelta(days=3), time(21, 5)),
                "manual",
            ),
            (
                "sample-record-behavior",
                "sample-pet-choco",
                "behavior",
                "낯선 소리 반응",
                "초인종 소리에 잠깐 짖었지만 금방 보호자 옆에서 진정했어요.",
                "normal",
                _at(base_date - timedelta(days=4), time(17, 40)),
                "manual",
            ),
            (
                "sample-record-nabi-meal",
                "sample-pet-nabi",
                "meal",
                "습식 급여",
                "습식 사료는 잘 먹었지만 물은 평소보다 적게 마셨어요.",
                "notice",
                _at(base_date, time(7, 50)),
                "manual",
            ),
            (
                "sample-record-nabi-behavior",
                "sample-pet-nabi",
                "behavior",
                "숨는 행동",
                "청소기 소리가 난 뒤 침대 밑에 30분 정도 숨어 있었어요.",
                "notice",
                _at(base_date - timedelta(days=1), time(14, 30)),
                "manual",
            ),
            (
                "sample-record-ddang-walk",
                "sample-pet-ddang",
                "walk",
                "짧은 산책",
                "아침에 12분 정도 산책했고 다른 강아지를 보고 흥분했어요.",
                "normal",
                _at(base_date, time(9, 15)),
                "manual",
            ),
            (
                "sample-record-ddang-medical",
                "sample-pet-ddang",
                "medical",
                "예방접종 후 관찰",
                "접종 부위를 만지면 살짝 예민해했지만 식욕은 괜찮았어요.",
                "notice",
                _at(base_date - timedelta(days=2), time(18, 0)),
                "manual",
            ),
        ),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO care_schedules (id, pet_id, category, title, due_date, repeat_label, note, is_done)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            (
                "sample-schedule-checkup",
                "sample-pet-choco",
                "checkup",
                "정기 검진",
                (base_date + timedelta(days=7)).isoformat(),
                "6개월마다",
                "최근 식사량과 배변 상태를 같이 상담하기",
                0,
            ),
            (
                "sample-schedule-grooming",
                "sample-pet-choco",
                "grooming",
                "미용 예약",
                (base_date + timedelta(days=3)).isoformat(),
                "필요 시",
                "발톱과 귀 상태 확인",
                0,
            ),
            (
                "sample-schedule-nabi-checkup",
                "sample-pet-nabi",
                "checkup",
                "음수량 상담",
                (base_date + timedelta(days=5)).isoformat(),
                "필요 시",
                "최근 물 마시는 양이 줄었는지 상담하기",
                0,
            ),
            (
                "sample-schedule-ddang-vaccination",
                "sample-pet-ddang",
                "vaccination",
                "추가 접종 확인",
                (base_date + timedelta(days=10)).isoformat(),
                "수의사 안내",
                "예방접종 후 상태와 다음 접종 일정 확인",
                0,
            ),
        ),
    )
    connection.commit()


def _at(day: date, value: time) -> str:
    return datetime.combine(day, value).isoformat()


if __name__ == "__main__":
    seed_database()

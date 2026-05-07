import json
import tempfile
import unittest
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from domain.models import StructuredRecordCandidate
from infrastructure.database import connect
from infrastructure.repositories import PetProfileRepository, RecordRepository, ScheduleRepository
from infrastructure.seed_data import SAMPLE_PET_ID, SAMPLE_PET_IDS, seed_database, seed_default_data


class TestDatabaseRepositories(unittest.TestCase):
    def test_connect_seeds_file_database_once_when_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "pet_log.sqlite3"

            connection = connect(database_path)
            seeded_pet_count = connection.execute("SELECT COUNT(*) FROM pets").fetchone()[0]
            seeded_record_count = connection.execute("SELECT COUNT(*) FROM pet_records").fetchone()[0]
            connection.close()

            second_connection = connect(database_path)
            second_pet_count = second_connection.execute("SELECT COUNT(*) FROM pets").fetchone()[0]
            second_record_count = second_connection.execute("SELECT COUNT(*) FROM pet_records").fetchone()[0]
            second_connection.close()

        self.assertEqual(seeded_pet_count, 3)
        self.assertEqual(seeded_record_count, 9)
        self.assertEqual(second_pet_count, 3)
        self.assertEqual(second_record_count, 9)

    def test_seed_default_data_adds_three_korean_sample_pets(self):
        connection = connect(":memory:")
        seed_default_data(connection, today=date(2026, 5, 7))

        pets = {
            row["id"]: (row["name"], row["breed"], row["species"])
            for row in connection.execute("SELECT id, name, breed, species FROM pets ORDER BY id").fetchall()
        }

        self.assertEqual(tuple(sorted(pets)), tuple(sorted(SAMPLE_PET_IDS)))
        self.assertEqual(pets["sample-pet-choco"], ("초코", "말티푸", "dog"))
        self.assertEqual(pets["sample-pet-nabi"], ("나비", "코리안숏헤어", "cat"))
        self.assertEqual(pets["sample-pet-ddang"], ("땅콩", "포메라니안", "dog"))

    def test_seed_default_data_uses_run_date_relative_dates(self):
        connection = connect(":memory:")
        seed_default_data(connection, today=date(2026, 5, 7))

        pet = connection.execute(
            "SELECT name, breed, personality, notes FROM pets WHERE id = ?",
            (SAMPLE_PET_ID,),
        ).fetchone()
        record_dates = tuple(
            row["recorded_at"]
            for row in connection.execute(
                "SELECT recorded_at FROM pet_records WHERE pet_id = ? ORDER BY recorded_at DESC",
                (SAMPLE_PET_ID,),
            ).fetchall()
        )
        record_titles = tuple(
            row["title"]
            for row in connection.execute(
                "SELECT title FROM pet_records WHERE pet_id = ? ORDER BY recorded_at DESC",
                (SAMPLE_PET_ID,),
            ).fetchall()
        )
        schedule_dates = tuple(
            row["due_date"]
            for row in connection.execute(
                "SELECT due_date FROM care_schedules WHERE pet_id = ? ORDER BY due_date",
                (SAMPLE_PET_ID,),
            ).fetchall()
        )
        schedule_titles = tuple(
            row["title"]
            for row in connection.execute(
                "SELECT title FROM care_schedules WHERE pet_id = ? ORDER BY due_date",
                (SAMPLE_PET_ID,),
            ).fetchall()
        )

        self.assertEqual(pet["name"], "초코")
        self.assertEqual(pet["breed"], "말티푸")
        self.assertIn("저녁 산책", pet["personality"])
        self.assertEqual(json.loads(pet["notes"]), ["아침 식사는 천천히 먹는 편", "알러지 의심 간식은 피하기"])
        self.assertEqual(record_dates[0], "2026-05-07T08:10:00")
        self.assertEqual(record_dates[-1], "2026-05-03T17:40:00")
        self.assertEqual(record_titles, ("아침 식사", "저녁 산책", "배변 상태", "귀 상태 확인", "낯선 소리 반응"))
        self.assertEqual(schedule_dates, ("2026-05-10", "2026-05-14"))
        self.assertEqual(schedule_titles, ("미용 예약", "정기 검진"))

    def test_seed_database_can_seed_existing_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "pet_log.sqlite3"
            database_path.touch()

            seed_database(database_path, today=date(2026, 5, 7))
            seeded_connection = connect(database_path)
            pet_count = seeded_connection.execute("SELECT COUNT(*) FROM pets").fetchone()[0]
            seeded_connection.close()

        self.assertEqual(pet_count, 3)

    def test_pet_profile_repository_reads_sqlite_pet(self):
        connection = connect(":memory:")
        connection.execute(
            """
            INSERT INTO pets (id, name, breed, species, age_label, personality, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("pet-1", "Choco", "Poodle", "dog", "3 years", "gentle", json.dumps(["likes walks"])),
        )
        connection.commit()
        repository = PetProfileRepository(connection=connection)

        pet = repository.get_pet("pet-1")

        self.assertEqual(pet.id, "pet-1")
        self.assertEqual(pet.name, "Choco")
        self.assertEqual(pet.breed, "Poodle")
        self.assertEqual(pet.species, "dog")
        self.assertEqual(pet.notes, ("likes walks",))

    def test_record_repository_saves_and_reads_sqlite_records(self):
        connection = connect(":memory:")
        repository = RecordRepository(connection=connection)
        candidate = StructuredRecordCandidate(
            title="Morning meal",
            detail="Ate half of breakfast",
            category="meal",
            status="notice",
            confidence=0.8,
            needs_confirmation=False,
        )

        saved = repository.save_candidate("pet-1", candidate)

        self.assertEqual(saved.pet_id, "pet-1")
        self.assertEqual(saved.title, "Morning meal")
        self.assertEqual(saved.source, "ai_preview")
        self.assertEqual(repository.list_recent("pet-1", lookback_days=30), (saved,))
        self.assertEqual(repository.list_by_ids("pet-1", (saved.id,)), (saved,))
        self.assertEqual(repository.list_recent("pet-2", lookback_days=30), ())

    def test_record_repository_preserves_requested_id_order(self):
        connection = connect(":memory:")
        connection.executemany(
            """
            INSERT INTO pet_records (id, pet_id, category, title, detail, status, recorded_at, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ("record-1", "pet-1", "meal", "Meal", "Ate well", "normal", "2026-05-06T08:00:00", "manual"),
                ("record-2", "pet-1", "walk", "Walk", "Park", "normal", "2026-05-06T09:00:00", "manual"),
            ),
        )
        connection.commit()
        repository = RecordRepository(connection=connection)

        records = repository.list_by_ids("pet-1", ("record-2", "record-1"))

        self.assertEqual(tuple(record.id for record in records), ("record-2", "record-1"))

    def test_schedule_repository_reads_due_sqlite_items(self):
        connection = connect(":memory:")
        today = datetime.now(UTC).date()
        due_date = (today + timedelta(days=2)).isoformat()
        later_date = (today + timedelta(days=20)).isoformat()
        connection.executemany(
            """
            INSERT INTO care_schedules (id, pet_id, category, title, due_date, repeat_label, note, is_done)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ("schedule-1", "pet-1", "checkup", "Checkup", due_date, "", "Regular visit", 0),
                ("schedule-2", "pet-1", "grooming", "Grooming", later_date, "", "Too far away", 0),
                ("schedule-3", "pet-1", "food", "Food order", due_date, "", "Already done", 1),
            ),
        )
        connection.commit()
        repository = ScheduleRepository(connection=connection)

        due_items = repository.list_due_items("pet-1", days_ahead=14)

        self.assertEqual(len(due_items), 1)
        self.assertEqual(due_items[0].title, "Checkup")
        self.assertEqual(due_items[0].due_date, due_date)
        self.assertEqual(due_items[0].reason, "Regular visit")


if __name__ == "__main__":
    unittest.main()

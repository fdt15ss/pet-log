import json
import sqlite3
import tempfile
import threading
import unittest
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from domain.models import StructuredRecordCandidate
from infrastructure.database import connect, initialize_schema
from infrastructure.repositories import (
    CommunityRepository,
    FileRepository,
    PetProfileRepository,
    RecordRepository,
    ScheduleRepository,
)
from infrastructure.repositories.file_repository import LocalFileStorage
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

    def test_connect_seeds_existing_file_when_default_sample_pet_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "pet_log.sqlite3"
            connection = connect(database_path)
            connection.execute("DELETE FROM pets WHERE id = ?", (SAMPLE_PET_ID,))
            connection.commit()
            connection.close()

            seeded_connection = connect(database_path)
            sample_pet = seeded_connection.execute(
                "SELECT id FROM pets WHERE id = ?",
                (SAMPLE_PET_ID,),
            ).fetchone()
            seeded_connection.close()

        self.assertIsNotNone(sample_pet)

    def test_connect_seeds_existing_file_when_default_community_posts_are_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "pet_log.sqlite3"
            connection = connect(database_path)
            connection.execute("DELETE FROM community_comments")
            connection.execute("DELETE FROM community_posts")
            connection.commit()
            connection.close()

            seeded_connection = connect(database_path)
            community_post_count = seeded_connection.execute(
                "SELECT COUNT(*) FROM community_posts WHERE deleted_at IS NULL",
            ).fetchone()[0]
            seeded_connection.close()

        self.assertEqual(community_post_count, 5)

    def test_seed_default_data_adds_three_korean_sample_pets(self):
        connection = connect(":memory:")
        seed_default_data(connection, today=date(2026, 5, 7))

        pets = {
            row["id"]: (row["name"], row["breed"], row["species"])
            for row in connection.execute("SELECT id, name, breed, species FROM pets ORDER BY id").fetchall()
        }

        self.assertEqual(tuple(sorted(pets)), tuple(sorted(SAMPLE_PET_IDS)))
        self.assertEqual(pets["pet_01JCM7V8H9Q2K4N6R8T0A1B2C3"], ("초코", "말티푸", "dog"))
        self.assertEqual(pets["pet_01JCM7V8H9Q2K4N6R8T0D4E5F6"], ("나비", "코리안숏헤어", "cat"))
        self.assertEqual(pets["pet_01JCM7V8H9Q2K4N6R8T0G7H8J9"], ("땅콩", "포메라니안", "dog"))

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

    def test_seed_default_data_adds_sample_notifications(self):
        connection = connect(":memory:")
        seed_default_data(connection, today=date(2026, 5, 7))

        notifications = connection.execute(
            """
            SELECT id, category, title, detail, action, action_href, due_label, tone, dedupe_key
            FROM notifications
            WHERE pet_id = ?
            ORDER BY id
            """,
            (SAMPLE_PET_ID,),
        ).fetchall()
        notifications_by_id = {notification["id"]: notification for notification in notifications}

        self.assertEqual(
            {
                "sample-notification-behavior-change",
                "sample-notification-missing-record",
                "sample-notification-risk",
            },
            set(notifications_by_id),
        )

        missing_record = notifications_by_id["sample-notification-missing-record"]
        self.assertEqual(missing_record["category"], "기록")
        self.assertEqual(missing_record["title"], "기록 누락 알림")
        self.assertIn("식사, 산책, 배변", missing_record["detail"])
        self.assertEqual(missing_record["action"], "기록 추가")
        self.assertEqual(missing_record["action_href"], "/record")
        self.assertEqual(missing_record["due_label"], "오늘")
        self.assertEqual(missing_record["tone"], "orange")
        self.assertEqual(missing_record["dedupe_key"], "sample:missing_record:daily-care")

        risk = notifications_by_id["sample-notification-risk"]
        self.assertEqual(risk["category"], "주의")
        self.assertEqual(risk["title"], "주의 기록 확인")
        self.assertIn("귀를 긁는 행동", risk["detail"])
        self.assertEqual(risk["action"], "기록 확인")
        self.assertEqual(risk["action_href"], "/timeline")
        self.assertEqual(risk["due_label"], "오늘")
        self.assertEqual(risk["tone"], "red")
        self.assertEqual(risk["dedupe_key"], "sample:risk:ear-scratch")

        behavior_change = notifications_by_id["sample-notification-behavior-change"]
        self.assertEqual(behavior_change["category"], "행동 변화")
        self.assertEqual(behavior_change["title"], "행동 변화 관찰")
        self.assertIn("낯선 소리 반응", behavior_change["detail"])
        self.assertEqual(behavior_change["action"], "기록 확인")
        self.assertEqual(behavior_change["action_href"], "/timeline")
        self.assertEqual(behavior_change["due_label"], "오늘")
        self.assertEqual(behavior_change["tone"], "orange")
        self.assertEqual(behavior_change["dedupe_key"], "sample:behavior_change:sound-reaction")

    def test_seed_database_can_seed_existing_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "pet_log.sqlite3"
            database_path.touch()

            seed_database(database_path, today=date(2026, 5, 7))
            seeded_connection = connect(database_path)
            pet_count = seeded_connection.execute("SELECT COUNT(*) FROM pets").fetchone()[0]
            seeded_connection.close()

        self.assertEqual(pet_count, 3)

    def test_initialize_schema_creates_file_storage_tables(self):
        connection = connect(":memory:")

        file_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(files)").fetchall()
        }
        pet_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(pets)").fetchall()
        }

        self.assertEqual(
            {
                "id",
                "owner_user_id",
                "pet_id",
                "purpose",
                "storage_key",
                "mime_type",
                "byte_size",
                "created_at",
                "deleted_at",
            },
            file_columns,
        )
        self.assertIn("photo_file_id", pet_columns)

    def test_initialize_schema_adds_photo_file_id_to_existing_pets_table(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute(
            """
            CREATE TABLE pets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT
            )
            """
        )

        initialize_schema(connection)
        pet_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(pets)").fetchall()
        }

        self.assertIn("photo_file_id", pet_columns)

    def test_initialize_schema_creates_community_tables(self):
        connection = connect(":memory:")

        post_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(community_posts)").fetchall()
        }
        comment_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(community_comments)").fetchall()
        }

        self.assertEqual(
            {
                "id",
                "board",
                "title",
                "body",
                "author_name",
                "created_at",
                "likes",
                "distance",
                "feeds",
                "tags",
                "deleted_at",
            },
            post_columns,
        )
        self.assertEqual(
            {
                "id",
                "post_id",
                "author_name",
                "body",
                "created_at",
                "deleted_at",
            },
            comment_columns,
        )

    def test_file_repository_saves_profile_photo_metadata(self):
        connection = connect(":memory:")
        repository = FileRepository(connection=connection)

        saved_file = repository.save_metadata(
            owner_user_id="user-1",
            pet_id="pet-1",
            purpose="profile_photo",
            storage_key="profile_photos/pet-1/file-1.jpg",
            mime_type="image/jpeg",
            byte_size=12,
            file_id="file-1",
        )

        self.assertEqual(saved_file.id, "file-1")
        self.assertEqual(saved_file.owner_user_id, "user-1")
        self.assertEqual(saved_file.pet_id, "pet-1")
        self.assertEqual(saved_file.purpose, "profile_photo")
        self.assertEqual(saved_file.storage_key, "profile_photos/pet-1/file-1.jpg")
        self.assertEqual(saved_file.mime_type, "image/jpeg")
        self.assertEqual(saved_file.byte_size, 12)
        self.assertEqual(repository.get_file("file-1"), saved_file)

    def test_local_file_storage_writes_under_upload_root(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = LocalFileStorage(Path(directory))

            saved_path = storage.write("profile_photos/pet-1/file-1.jpg", b"image-bytes")

            self.assertEqual(
                saved_path,
                (Path(directory) / "profile_photos" / "pet-1" / "file-1.jpg").resolve(),
            )
            self.assertEqual(saved_path.read_bytes(), b"image-bytes")

    def test_pet_profile_repository_reads_sqlite_pet(self):
        connection = connect(":memory:")
        connection.execute(
            """
            INSERT INTO pets (id, name, breed, species, age_label, sex_label, weight_label, birthday, personality, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("pet-1", "Choco", "Poodle", "dog", "3 years", "female", "3.4kg", "2018.5.11", "gentle", json.dumps(["likes walks"])),
        )
        connection.commit()
        repository = PetProfileRepository(connection=connection)

        pet = repository.get_pet("pet-1")

        self.assertEqual(pet.id, "pet-1")
        self.assertEqual(pet.name, "Choco")
        self.assertEqual(pet.breed, "Poodle")
        self.assertEqual(pet.species, "dog")
        self.assertEqual(pet.sex_label, "female")
        self.assertEqual(pet.weight_label, "3.4kg")
        self.assertEqual(pet.birthday, "2018.5.11")
        self.assertEqual(pet.notes, ("likes walks",))

    def test_sqlite_connection_can_be_used_from_fastapi_worker_thread(self):
        connection = connect(":memory:")
        connection.execute(
            """
            INSERT INTO pets (id, name, breed, species, age_label, personality, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("pet-thread", "Thread Choco", "Poodle", "dog", "3 years", "gentle", json.dumps([])),
        )
        connection.commit()
        repository = PetProfileRepository(connection=connection)
        result: dict[str, object] = {}

        def read_pet() -> None:
            try:
                result["pet"] = repository.get_pet("pet-thread")
            except Exception as exc:  # pragma: no cover - asserted below
                result["error"] = exc

        thread = threading.Thread(target=read_pet)
        thread.start()
        thread.join()

        self.assertNotIn("error", result)
        self.assertEqual(result["pet"].name, "Thread Choco")

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

        saved = repository.save_candidate("pet-1", candidate, source="manual")

        self.assertEqual(saved.pet_id, "pet-1")
        self.assertEqual(saved.title, "Morning meal")
        self.assertEqual(saved.source, "manual")
        self.assertEqual(repository.list_recent("pet-1", lookback_days=30), (saved,))
        self.assertEqual(repository.list_by_ids("pet-1", (saved.id,)), (saved,))
        self.assertEqual(repository.list_recent("pet-2", lookback_days=30), ())

    def test_record_repository_filters_sqlite_records_by_lookback_days(self):
        connection = connect(":memory:")
        recent_at = _days_ago(1)
        old_at = _days_ago(40)
        connection.executemany(
            """
            INSERT INTO pet_records (id, pet_id, category, title, detail, status, recorded_at, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ("record-old", "pet-1", "meal", "Old meal", "Ate last month", "normal", old_at, "manual"),
                ("record-recent", "pet-1", "meal", "Recent meal", "Ate today", "normal", recent_at, "manual"),
            ),
        )
        connection.commit()
        repository = RecordRepository(connection=connection)

        records = repository.list_recent("pet-1", lookback_days=30)

        self.assertEqual(tuple(record.id for record in records), ("record-recent",))

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

    def test_community_repository_lists_seed_posts_by_feed_and_board(self):
        connection = connect(":memory:")
        seed_default_data(connection, today=date(2026, 5, 7))
        repository = CommunityRepository(connection=connection)

        posts = repository.list_posts(feed="인기글", board="행동 고민")

        self.assertEqual(tuple(post.id for post in posts), ("c1",))
        self.assertEqual(posts[0].board, "행동 고민")
        self.assertEqual(posts[0].comments, 2)
        self.assertEqual(posts[0].likes, 26)
        self.assertIn("산책", posts[0].tags)

    def test_community_repository_creates_comment_and_increments_count(self):
        connection = connect(":memory:")
        seed_default_data(connection, today=date(2026, 5, 7))
        repository = CommunityRepository(connection=connection)

        comment = repository.create_comment(post_id="c1", body="같이 기록해보겠습니다.", author_name="나")

        detail = repository.get_post("c1")
        self.assertIsNotNone(detail)
        self.assertEqual(comment.post_id, "c1")
        self.assertEqual(comment.body, "같이 기록해보겠습니다.")
        self.assertEqual(detail.comments, 3)

    def test_community_repository_creates_post_and_adds_reaction(self):
        connection = connect(":memory:")
        repository = CommunityRepository(connection=connection)

        post = repository.create_post(board="자유게시판", title="새 글", body="본문입니다.", author_name="나")
        reacted = repository.add_reaction(post.id)

        self.assertEqual(post.feeds, ("최신글",))
        self.assertEqual(post.tags, ("새 글",))
        self.assertEqual(reacted.likes, 1)

    def test_community_repository_uses_custom_post_tags(self):
        connection = connect(":memory:")
        repository = CommunityRepository(connection=connection)

        post = repository.create_post(
            board="자유게시판",
            title="새 글",
            body="본문입니다.",
            author_name="나",
            tags=("입양", "임시보호"),
        )

        self.assertEqual(post.tags, ("입양", "임시보호"))

    def test_community_repository_lists_popular_posts_from_ten_likes(self):
        connection = connect(":memory:")
        repository = CommunityRepository(connection=connection)

        post = repository.create_post(board="자유게시판", title="인기 후보", body="본문입니다.", author_name="나")
        for _ in range(9):
            repository.add_reaction(post.id)

        popular_before = repository.list_posts(feed="인기글", board="자유게시판")
        self.assertNotIn(post.id, tuple(item.id for item in popular_before))

        repository.add_reaction(post.id)

        popular_after = repository.list_posts(feed="인기글", board="자유게시판")
        self.assertIn(post.id, tuple(item.id for item in popular_after))

    def test_community_repository_stores_created_post_time_as_iso_timestamp(self):
        connection = connect(":memory:")
        repository = CommunityRepository(connection=connection)

        post = repository.create_post(board="자유게시판", title="새 글", body="본문입니다.", author_name="나")

        parsed = datetime.fromisoformat(post.created_at.replace("Z", "+00:00"))
        self.assertEqual(parsed.tzinfo, UTC)

    def test_community_repository_uses_random_nickname_when_author_is_omitted(self):
        connection = connect(":memory:")
        repository = CommunityRepository(connection=connection)

        post = repository.create_post(board="자유게시판", title="새 글", body="본문입니다.")
        comment = repository.create_comment(post_id=post.id, body="첫 댓글입니다.")

        self.assertRegex(post.author_name, r"^[가-힣]+ [가-힣]+$")
        self.assertRegex(comment.author_name, r"^[가-힣]+ [가-힣]+$")
        self.assertNotEqual(post.author_name, "나")
        self.assertNotEqual(comment.author_name, "나")

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


def _days_ago(days: int) -> str:
    value = datetime.now(UTC) - timedelta(days=days)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    unittest.main()

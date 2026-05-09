from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(
    os.environ.get(
        "PET_LOG_DATABASE_PATH",
        Path(__file__).resolve().parents[2] / "pet_log.sqlite3",
    )
)


def connect(database_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(database_path) if database_path is not None else DEFAULT_DATABASE_PATH
    should_seed = path != Path(":memory:") and not path.exists()
    if path != Path(":memory:"):
        path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    initialize_schema(connection)
    if should_seed:
        from infrastructure.seed_data import seed_default_data

        seed_default_data(connection)
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS pet_records (
            id TEXT PRIMARY KEY,
            pet_id TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL,
            status TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_pet_records_pet_recorded_at
            ON pet_records (pet_id, recorded_at);

        CREATE TABLE IF NOT EXISTS pets (
            id TEXT PRIMARY KEY,
            owner_user_id TEXT,
            name TEXT NOT NULL,
            breed TEXT,
            species TEXT,
            age_label TEXT,
            sex_label TEXT,
            weight_label TEXT,
            birthday TEXT,
            personality TEXT,
            notes TEXT NOT NULL DEFAULT '[]',
            photo_file_id TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS care_schedules (
            id TEXT PRIMARY KEY,
            pet_id TEXT NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL,
            repeat_label TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            is_done INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_care_schedules_pet_due_date
            ON care_schedules (pet_id, due_date);
        """
    )
    connection.commit()

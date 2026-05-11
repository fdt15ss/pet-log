from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from domain.models import Notification
from infrastructure.database import initialize_schema


class NotificationRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        initialize_schema(self._connection)

    def list_for_pet(self, pet_id: str, limit: int = 50) -> tuple[Notification, ...]:
        rows = self._connection.execute(
            """
            SELECT id, pet_id, category, title, detail, action, action_href, due_label, tone, read_at, created_at
            FROM notifications
            WHERE pet_id = ? AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (pet_id, limit),
        ).fetchall()
        return tuple(_notification_from_row(row) for row in rows)

    def mark_as_read(self, notification_id: str) -> bool:
        cursor = self._connection.execute(
            "UPDATE notifications SET read_at = CURRENT_TIMESTAMP WHERE id = ? AND read_at IS NULL",
            (notification_id,),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def mark_all_as_read(self, pet_id: str) -> int:
        cursor = self._connection.execute(
            "UPDATE notifications SET read_at = CURRENT_TIMESTAMP WHERE pet_id = ? AND read_at IS NULL",
            (pet_id,),
        )
        self._connection.commit()
        return cursor.rowcount

    def create(
        self,
        pet_id: str,
        category: str,
        title: str,
        detail: str,
        action: str,
        action_href: str,
        due_label: str,
        tone: str,
    ) -> Notification:
        notification_id = str(uuid4())
        created_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        self._connection.execute(
            """
            INSERT INTO notifications (id, pet_id, category, title, detail, action, action_href, due_label, tone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (notification_id, pet_id, category, title, detail, action, action_href, due_label, tone, created_at),
        )
        self._connection.commit()
        return Notification(
            id=notification_id,
            pet_id=pet_id,
            category=category,
            title=title,
            detail=detail,
            action=action,
            action_href=action_href,
            due_label=due_label,
            tone=tone,
            created_at=created_at,
        )


def _notification_from_row(row: sqlite3.Row) -> Notification:
    return Notification(
        id=row["id"],
        pet_id=row["pet_id"],
        category=row["category"],
        title=row["title"],
        detail=row["detail"],
        action=row["action"],
        action_href=row["action_href"],
        due_label=row["due_label"],
        tone=row["tone"],
        read_at=row["read_at"],
        created_at=row["created_at"],
    )

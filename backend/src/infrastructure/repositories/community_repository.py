from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from domain.models import CommunityComment, CommunityPost
from infrastructure.database import initialize_schema

COMMUNITY_BOARDS = ("유기동물", "용품 나눔", "자유게시판", "행동 고민", "후기")
COMMUNITY_FEEDS = ("인기글", "최신글", "내 주변")

_BOARD_ALIASES = {
    "반려용품 나눔": "용품 나눔",
}


class CommunityRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        initialize_schema(self._connection)

    def list_boards(self) -> tuple[str, ...]:
        return COMMUNITY_BOARDS

    def list_posts(self, feed: str | None = None, board: str | None = None) -> tuple[CommunityPost, ...]:
        board = _normalize_board(board) if board else None
        rows = self._connection.execute(
            """
            SELECT
                p.id, p.board, p.title, p.body, p.author_name, p.created_at, p.likes,
                p.distance, p.feeds, p.tags, COUNT(c.id) AS comment_count
            FROM community_posts p
            LEFT JOIN community_comments c
                ON c.post_id = p.id AND c.deleted_at IS NULL
            WHERE p.deleted_at IS NULL
            GROUP BY p.id
            ORDER BY p.created_at DESC, p.id DESC
            """
        ).fetchall()
        posts = tuple(_post_from_row(row) for row in rows)
        return tuple(
            post
            for post in posts
            if (feed is None or feed in post.feeds) and (board is None or post.board == board)
        )

    def get_post(self, post_id: str) -> CommunityPost | None:
        row = self._connection.execute(
            """
            SELECT
                p.id, p.board, p.title, p.body, p.author_name, p.created_at, p.likes,
                p.distance, p.feeds, p.tags, COUNT(c.id) AS comment_count
            FROM community_posts p
            LEFT JOIN community_comments c
                ON c.post_id = p.id AND c.deleted_at IS NULL
            WHERE p.id = ? AND p.deleted_at IS NULL
            GROUP BY p.id
            """,
            (post_id,),
        ).fetchone()
        if row is None:
            return None
        return _post_from_row(row)

    def list_comments(self, post_id: str) -> tuple[CommunityComment, ...]:
        rows = self._connection.execute(
            """
            SELECT id, post_id, author_name, body, created_at
            FROM community_comments
            WHERE post_id = ? AND deleted_at IS NULL
            ORDER BY created_at DESC, id DESC
            """,
            (post_id,),
        ).fetchall()
        return tuple(_comment_from_row(row) for row in rows)

    def create_post(self, board: str, title: str, body: str, author_name: str = "나") -> CommunityPost:
        post_id = f"community-{uuid4().hex}"
        created_at = "방금"
        board = _normalize_board(board)
        self._connection.execute(
            """
            INSERT INTO community_posts
                (id, board, title, body, author_name, created_at, likes, feeds, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_id,
                board,
                title.strip(),
                body.strip(),
                author_name,
                created_at,
                0,
                json.dumps(["최신글"], ensure_ascii=False),
                json.dumps(["새 글"], ensure_ascii=False),
            ),
        )
        self._connection.commit()
        post = self.get_post(post_id)
        if post is None:  # pragma: no cover - insert and read use same id
            raise RuntimeError("community post was not created")
        return post

    def create_comment(self, post_id: str, body: str, author_name: str = "나") -> CommunityComment:
        comment_id = f"comment-{post_id}-{uuid4().hex}"
        created_at = _now_label()
        self._connection.execute(
            """
            INSERT INTO community_comments (id, post_id, author_name, body, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (comment_id, post_id, author_name, body.strip(), created_at),
        )
        self._connection.commit()
        return CommunityComment(
            id=comment_id,
            post_id=post_id,
            author_name=author_name,
            body=body.strip(),
            created_at=created_at,
        )

    def add_reaction(self, post_id: str) -> CommunityPost:
        cursor = self._connection.execute(
            "UPDATE community_posts SET likes = likes + 1 WHERE id = ? AND deleted_at IS NULL",
            (post_id,),
        )
        self._connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(post_id)
        post = self.get_post(post_id)
        if post is None:  # pragma: no cover - update already matched the row
            raise KeyError(post_id)
        return post


def _post_from_row(row: sqlite3.Row) -> CommunityPost:
    return CommunityPost(
        id=row["id"],
        board=row["board"],
        title=row["title"],
        body=row["body"],
        author_name=row["author_name"],
        created_at=row["created_at"],
        comments=row["comment_count"],
        likes=row["likes"],
        distance=row["distance"],
        feeds=tuple(json.loads(row["feeds"] or "[]")),
        tags=tuple(json.loads(row["tags"] or "[]")),
    )


def _comment_from_row(row: sqlite3.Row) -> CommunityComment:
    return CommunityComment(
        id=row["id"],
        post_id=row["post_id"],
        author_name=row["author_name"],
        body=row["body"],
        created_at=row["created_at"],
    )


def _normalize_board(board: str) -> str:
    return _BOARD_ALIASES.get(board, board)


def _now_label() -> str:
    now = datetime.now(UTC)
    return now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from domain.enums import CommunityBoard, CommunityFeed, CommunityReactionType
from domain.models import CommunityComment, CommunityPost, CommunityReaction
from infrastructure.database import initialize_schema

POPULAR_SCORE_THRESHOLD = 10


class CommunityRepository:
    def __init__(
        self,
        posts: tuple[CommunityPost, ...] = (),
        comments: tuple[CommunityComment, ...] = (),
        reactions: tuple[CommunityReaction, ...] = (),
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._connection = connection
        if self._connection is not None:
            initialize_schema(self._connection)
        self._posts = list(posts)
        self._comments = list(comments)
        self._reactions = list(reactions)

    def list_posts(
        self,
        feed: CommunityFeed | None = None,
        board: CommunityBoard | None = None,
    ) -> tuple[CommunityPost, ...]:
        posts = self._all_posts(board=board)
        filtered = tuple(post for post in posts if feed is None or feed in post.feeds)
        if feed == "인기글":
            return tuple(sorted(filtered, key=lambda post: (post.likes + post.comments, post.created_at, post.id), reverse=True))
        return tuple(sorted(filtered, key=lambda post: (post.created_at, post.id), reverse=True))

    def get_post(self, post_id: str) -> CommunityPost:
        if self._connection is not None:
            row = self._connection.execute(
                """
                SELECT id, board, title, body, author_name, created_at, comment_count, like_count, distance, tags
                FROM community_posts
                WHERE id = ? AND deleted_at IS NULL
                """,
                (post_id,),
            ).fetchone()
            if row is None:
                raise KeyError(post_id)
            return _post_from_row(row)

        for post in self._posts:
            if post.id == post_id:
                return post
        raise KeyError(post_id)

    def create_post(
        self,
        board: CommunityBoard,
        title: str,
        body: str,
        author_name: str = "나",
        distance: str | None = None,
        tags: tuple[str, ...] = (),
        created_at: str | None = None,
        post_id: str | None = None,
    ) -> CommunityPost:
        saved_post = CommunityPost(
            id=post_id or self._next_post_id(),
            board=board,
            title=title.strip(),
            body=body.strip(),
            author_name=author_name.strip(),
            created_at=created_at or _utc_now(),
            distance=distance.strip() if distance else None,
            tags=tuple(tag.strip() for tag in tags if tag.strip()),
        )
        saved_post = _with_computed_feeds(saved_post)
        if self._connection is not None:
            self._connection.execute(
                """
                INSERT INTO community_posts (id, board, title, body, author_name, created_at, distance, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    saved_post.id,
                    saved_post.board,
                    saved_post.title,
                    saved_post.body,
                    saved_post.author_name,
                    saved_post.created_at,
                    saved_post.distance,
                    json.dumps(list(saved_post.tags), ensure_ascii=False),
                ),
            )
            self._connection.commit()
            return saved_post

        self._posts.append(saved_post)
        return saved_post

    def list_comments(self, post_id: str) -> tuple[CommunityComment, ...]:
        if self._connection is not None:
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

        return tuple(reversed([comment for comment in self._comments if comment.post_id == post_id]))

    def add_comment(
        self,
        post_id: str,
        body: str,
        author_name: str = "나",
        created_at: str | None = None,
        comment_id: str | None = None,
    ) -> CommunityComment:
        self.get_post(post_id)
        saved_comment = CommunityComment(
            id=comment_id or self._next_comment_id(post_id),
            post_id=post_id,
            author_name=author_name.strip(),
            body=body.strip(),
            created_at=created_at or _utc_now(),
        )
        if self._connection is not None:
            self._connection.execute(
                """
                INSERT INTO community_comments (id, post_id, author_name, body, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    saved_comment.id,
                    saved_comment.post_id,
                    saved_comment.author_name,
                    saved_comment.body,
                    saved_comment.created_at,
                ),
            )
            self._connection.execute(
                "UPDATE community_posts SET comment_count = comment_count + 1 WHERE id = ?",
                (post_id,),
            )
            self._connection.commit()
            return saved_comment

        self._comments.append(saved_comment)
        self._replace_post(post_id, comments=self.get_post(post_id).comments + 1)
        return saved_comment

    def add_reaction(
        self,
        post_id: str,
        reaction_type: CommunityReactionType = "like",
        created_at: str | None = None,
        reaction_id: str | None = None,
    ) -> CommunityReaction:
        self.get_post(post_id)
        saved_reaction = CommunityReaction(
            id=reaction_id or self._next_reaction_id(post_id),
            post_id=post_id,
            reaction_type=reaction_type,
            created_at=created_at or _utc_now(),
        )
        if self._connection is not None:
            self._connection.execute(
                """
                INSERT INTO community_reactions (id, post_id, reaction_type, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    saved_reaction.id,
                    saved_reaction.post_id,
                    saved_reaction.reaction_type,
                    saved_reaction.created_at,
                ),
            )
            self._connection.execute(
                "UPDATE community_posts SET like_count = like_count + 1 WHERE id = ?",
                (post_id,),
            )
            self._connection.commit()
            return saved_reaction

        self._reactions.append(saved_reaction)
        self._replace_post(post_id, likes=self.get_post(post_id).likes + 1)
        return saved_reaction

    def _all_posts(self, board: CommunityBoard | None = None) -> tuple[CommunityPost, ...]:
        if self._connection is not None:
            if board is None:
                rows = self._connection.execute(
                    """
                    SELECT id, board, title, body, author_name, created_at, comment_count, like_count, distance, tags
                    FROM community_posts
                    WHERE deleted_at IS NULL
                    """
                ).fetchall()
            else:
                rows = self._connection.execute(
                    """
                    SELECT id, board, title, body, author_name, created_at, comment_count, like_count, distance, tags
                    FROM community_posts
                    WHERE board = ? AND deleted_at IS NULL
                    """,
                    (board,),
                ).fetchall()
            return tuple(_post_from_row(row) for row in rows)

        return tuple(post for post in self._posts if board is None or post.board == board)

    def _next_post_id(self) -> str:
        if self._connection is not None:
            row = self._connection.execute("SELECT COUNT(*) FROM community_posts").fetchone()
            return f"community-{int(row[0]) + 1}"
        return f"community-{len(self._posts) + 1}"

    def _next_comment_id(self, post_id: str) -> str:
        if self._connection is not None:
            row = self._connection.execute(
                "SELECT COUNT(*) FROM community_comments WHERE post_id = ?",
                (post_id,),
            ).fetchone()
            return f"comment-{post_id}-{int(row[0]) + 1}"
        count = len([comment for comment in self._comments if comment.post_id == post_id])
        return f"comment-{post_id}-{count + 1}"

    def _next_reaction_id(self, post_id: str) -> str:
        if self._connection is not None:
            row = self._connection.execute(
                "SELECT COUNT(*) FROM community_reactions WHERE post_id = ?",
                (post_id,),
            ).fetchone()
            return f"reaction-{post_id}-{int(row[0]) + 1}"
        count = len([reaction for reaction in self._reactions if reaction.post_id == post_id])
        return f"reaction-{post_id}-{count + 1}"

    def _replace_post(self, post_id: str, comments: int | None = None, likes: int | None = None) -> None:
        for index, post in enumerate(self._posts):
            if post.id == post_id:
                self._posts[index] = _with_computed_feeds(
                    CommunityPost(
                        id=post.id,
                        board=post.board,
                        title=post.title,
                        body=post.body,
                        author_name=post.author_name,
                        created_at=post.created_at,
                        comments=comments if comments is not None else post.comments,
                        likes=likes if likes is not None else post.likes,
                        distance=post.distance,
                        tags=post.tags,
                    )
                )
                return


def _post_from_row(row: sqlite3.Row) -> CommunityPost:
    return _with_computed_feeds(
        CommunityPost(
            id=row["id"],
            board=row["board"],
            title=row["title"],
            body=row["body"],
            author_name=row["author_name"],
            created_at=row["created_at"],
            comments=row["comment_count"],
            likes=row["like_count"],
            distance=row["distance"],
            tags=tuple(json.loads(row["tags"] or "[]")),
        )
    )


def _comment_from_row(row: sqlite3.Row) -> CommunityComment:
    return CommunityComment(
        id=row["id"],
        post_id=row["post_id"],
        author_name=row["author_name"],
        body=row["body"],
        created_at=row["created_at"],
    )


def _with_computed_feeds(post: CommunityPost) -> CommunityPost:
    feeds: list[CommunityFeed] = ["최신글"]
    if post.likes + post.comments >= POPULAR_SCORE_THRESHOLD:
        feeds.insert(0, "인기글")
    if post.distance:
        feeds.append("내 주변")
    return CommunityPost(
        id=post.id,
        board=post.board,
        title=post.title,
        body=post.body,
        author_name=post.author_name,
        created_at=post.created_at,
        comments=post.comments,
        likes=post.likes,
        distance=post.distance,
        tags=post.tags,
        feeds=tuple(feeds),
    )


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

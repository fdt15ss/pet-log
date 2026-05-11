from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient

from infrastructure.database import connect
from infrastructure.repositories.community_repository import CommunityRepository
from infrastructure.seed_data import seed_default_data
from presentation.http.community_routes import build_community_router


BOARDS = ("유기동물", "용품 나눔", "자유게시판", "행동 고민", "후기")


def main() -> None:
    load_dotenv(override=False)
    connection = connect(":memory:")
    seed_default_data(connection, today=date(2026, 5, 11))
    repository = CommunityRepository(connection=connection)

    app = FastAPI()
    app.state.app_context = SimpleNamespace(community_repository=repository)
    app.include_router(build_community_router())

    try:
        with TestClient(app) as client:
            print("[manual smoke] community api")
            print("boards:", ", ".join(BOARDS))
            print()
            smoke_latest_posts(client)
            print()
            smoke_board_filter(client)
            print()
            smoke_create_comment_reaction(client)
    finally:
        connection.close()


def smoke_latest_posts(client: TestClient) -> None:
    response = client.get("/api/v1/community/posts", params={"feed": "최신글"})
    response.raise_for_status()
    posts = response.json()["data"]["posts"]

    print("[GET latest]")
    print("result count:", len(posts))
    _print_posts(posts[:3])


def smoke_board_filter(client: TestClient) -> None:
    response = client.get(
        "/api/v1/community/posts",
        params={"feed": "인기글", "board": "행동 고민"},
    )
    response.raise_for_status()
    posts = response.json()["data"]["posts"]

    print("[GET popular behavior board]")
    print("result count:", len(posts))
    _print_posts(posts)


def smoke_create_comment_reaction(client: TestClient) -> None:
    post_response = client.post(
        "/api/v1/community/posts",
        json={
            "board": "후기",
            "title": "커뮤니티 API 스모크 후기",
            "body": "백엔드 커뮤니티 작성 흐름을 확인합니다.",
            "author_name": "스모크",
            "tags": ["smoke", "api"],
        },
    )
    post_response.raise_for_status()
    post = post_response.json()["data"]["post"]

    comment_response = client.post(
        f"/api/v1/community/posts/{post['id']}/comments",
        json={"body": "댓글 작성 흐름도 확인합니다.", "author_name": "스모크"},
    )
    comment_response.raise_for_status()

    reaction_response = client.post(
        f"/api/v1/community/posts/{post['id']}/reactions",
        json={"reaction_type": "like"},
    )
    reaction_response.raise_for_status()
    updated_post = reaction_response.json()["data"]["post"]

    print("[POST post/comment/reaction]")
    print("created id:", post["id"])
    print("created board:", post["board"])
    print(f"updated counts: comments={updated_post['comments']} likes={updated_post['likes']}")


def _print_posts(posts: list[dict[str, object]]) -> None:
    for index, post in enumerate(posts, start=1):
        print(
            f"{index}. {post['board']} | {post['title']} | "
            f"comments={post['comments']} | likes={post['likes']} | feeds={','.join(post['feeds'])}"
        )


if __name__ == "__main__":
    main()

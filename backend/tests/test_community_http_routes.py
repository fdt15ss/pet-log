import unittest

from fastapi.testclient import TestClient

from infrastructure.repositories.community_repository import CommunityRepository
from presentation.http.app import create_app


class FakeAppContext:
    def __init__(self) -> None:
        self.community_repository = CommunityRepository()
        post = self.community_repository.create_post(
            board="행동 고민",
            title="산책 전 흥분을 어떻게 기록하나요?",
            body="현관 앞에서 기다리는 행동을 어떤 기준으로 남기면 좋을지 궁금합니다.",
            author_name="초코 보호자",
            tags=("산책", "행동"),
            created_at="2026-05-11T08:00:00Z",
        )
        self.community_repository.add_comment(
            post_id=post.id,
            body="시간과 상황을 같이 남기면 나중에 비교하기 좋았습니다.",
            author_name="두부네",
            created_at="2026-05-11T08:10:00Z",
        )

    def close(self) -> None:
        return None


class TestCommunityHttpRoutes(unittest.TestCase):
    def test_list_community_posts_returns_frontend_shape(self):
        context = FakeAppContext()

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.get("/api/v1/community/posts?feed=최신글&board=행동 고민")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "data": {
                    "posts": [
                        {
                            "id": "community-1",
                            "board": "행동 고민",
                            "title": "산책 전 흥분을 어떻게 기록하나요?",
                            "body": "현관 앞에서 기다리는 행동을 어떤 기준으로 남기면 좋을지 궁금합니다.",
                            "authorName": "초코 보호자",
                            "createdAt": "2026-05-11T08:00:00Z",
                            "comments": 1,
                            "likes": 0,
                            "distance": None,
                            "feeds": ["최신글"],
                            "tags": ["산책", "행동"],
                        }
                    ]
                },
            },
        )

    def test_get_community_post_detail_returns_comments(self):
        context = FakeAppContext()

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.get("/api/v1/community/posts/community-1")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["data"]["post"]["id"], "community-1")
        self.assertEqual(payload["data"]["comments"][0]["postId"], "community-1")
        self.assertEqual(payload["data"]["comments"][0]["authorName"], "두부네")

    def test_create_community_post_returns_created_post(self):
        context = FakeAppContext()

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            response = client.post(
                "/api/v1/community/posts",
                json={
                    "board": "후기",
                    "title": "짧은 산책을 나눈 후기",
                    "body": "아침과 저녁으로 나눴더니 안정되는 시간이 빨라졌습니다.",
                    "author_name": "밤산책",
                    "tags": ["산책"],
                },
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["post"]["id"], "community-2")
        self.assertEqual(response.json()["data"]["post"]["authorName"], "밤산책")
        self.assertEqual(response.json()["data"]["post"]["feeds"], ["최신글"])

    def test_create_comment_and_reaction_update_post_counts(self):
        context = FakeAppContext()

        with TestClient(create_app(app_context_factory=lambda: context)) as client:
            comment_response = client.post(
                "/api/v1/community/posts/community-1/comments",
                json={"body": "저도 같은 방식으로 남겨보겠습니다.", "author_name": "나"},
            )
            reaction_response = client.post(
                "/api/v1/community/posts/community-1/reactions",
                json={"reaction_type": "like"},
            )

        self.assertEqual(comment_response.status_code, 201)
        self.assertEqual(comment_response.json()["data"]["comment"]["id"], "comment-community-1-2")
        self.assertEqual(reaction_response.status_code, 200)
        self.assertEqual(reaction_response.json()["data"]["post"]["comments"], 2)
        self.assertEqual(reaction_response.json()["data"]["post"]["likes"], 1)

    def test_community_routes_return_404_for_missing_post(self):
        with TestClient(create_app(app_context_factory=FakeAppContext)) as client:
            response = client.get("/api/v1/community/posts/missing-post")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Community post not found"})


if __name__ == "__main__":
    unittest.main()

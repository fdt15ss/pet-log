import unittest

from infrastructure.database import connect
from infrastructure.repositories.community_repository import CommunityRepository


class TestCommunityRepository(unittest.TestCase):
    def test_create_post_lists_latest_and_board_filtered_posts(self):
        connection = connect(":memory:")
        repository = CommunityRepository(connection=connection)

        behavior_post = repository.create_post(
            board="행동 고민",
            title="산책 전 흥분을 어떻게 기록하나요?",
            body="현관 앞에서 기다리는 행동을 어떤 기준으로 남기면 좋을지 궁금합니다.",
            author_name="초코 보호자",
            tags=("산책", "행동"),
        )
        repository.create_post(
            board="후기",
            title="짧은 산책을 나눈 후기",
            body="아침과 저녁으로 나눠보니 밤에 안정되는 시간이 빨라졌습니다.",
            author_name="밤산책",
        )

        latest_posts = repository.list_posts(feed="최신글")
        board_posts = repository.list_posts(feed="최신글", board="행동 고민")

        self.assertEqual(tuple(post.id for post in latest_posts), ("community-2", "community-1"))
        self.assertEqual(board_posts, (behavior_post,))
        self.assertEqual(behavior_post.feeds, ("최신글",))
        self.assertEqual(behavior_post.tags, ("산책", "행동"))

    def test_list_posts_filters_popular_and_nearby_feeds(self):
        connection = connect(":memory:")
        repository = CommunityRepository(connection=connection)
        popular_post = repository.create_post(
            board="자유게시판",
            title="기록 루틴 공유",
            body="매일 같은 시간에 기록하니 변화가 더 잘 보였습니다.",
            author_name="두부네",
        )
        nearby_post = repository.create_post(
            board="용품 나눔",
            title="사용하지 않는 이동장 나눔",
            body="중형 반려동물용 이동장입니다. 직접 전달 가능합니다.",
            author_name="동네보호자",
            distance="1.2km",
        )
        for _ in range(10):
            repository.add_reaction(popular_post.id)

        popular_posts = repository.list_posts(feed="인기글")
        nearby_posts = repository.list_posts(feed="내 주변")

        self.assertEqual(tuple(post.id for post in popular_posts), (popular_post.id,))
        self.assertEqual(tuple(post.id for post in nearby_posts), (nearby_post.id,))
        self.assertEqual(repository.get_post(popular_post.id).likes, 10)

    def test_add_comment_increments_post_comment_count(self):
        connection = connect(":memory:")
        repository = CommunityRepository(connection=connection)
        post = repository.create_post(
            board="유기동물",
            title="임시 보호 정보 공유",
            body="보호소 공지 확인 후 공유합니다.",
            author_name="동네보호자",
        )

        comment = repository.add_comment(
            post_id=post.id,
            body="공지 원문도 함께 확인해보겠습니다.",
            author_name="나",
        )

        self.assertEqual(comment.id, "comment-community-1-1")
        self.assertEqual(comment.post_id, post.id)
        self.assertEqual(repository.get_post(post.id).comments, 1)
        self.assertEqual(repository.list_comments(post.id), (comment,))

    def test_get_post_raises_key_error_for_missing_post(self):
        repository = CommunityRepository()

        with self.assertRaises(KeyError):
            repository.get_post("missing-post")


if __name__ == "__main__":
    unittest.main()

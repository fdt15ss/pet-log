import { strict as assert } from "node:assert";
import { communityComments, communityPosts } from "./mock-data";
import { createCommunityComment, createCommunityPost, getCommunityPostDetail, getCommunityPosts } from "./community";

const popularPosts = getCommunityPosts(communityPosts, { feed: "인기글", board: null });

assert.equal(popularPosts.length, 3);
assert.equal(popularPosts[0].id, "c1");

const boardPosts = getCommunityPosts(communityPosts, { feed: "최신글", board: "후기" });

assert.deepEqual(
  boardPosts.map((post) => post.id),
  ["c4"],
);

const detail = getCommunityPostDetail(communityPosts[0], communityComments);

assert.equal(detail.commentItems.length, 2);
assert.equal(detail.meta, "행동 고민 · 댓글 8 · 공감 26");
assert.ok(detail.body.includes("산책 시간이 줄어든 뒤"));

const newComment = createCommunityComment({
  postId: "c1",
  body: "짧은 산책을 두 번으로 나누니 도움이 됐어요.",
  createdAt: "방금",
});

assert.equal(newComment.postId, "c1");
assert.equal(newComment.authorName, "나");

const newPost = createCommunityPost({
  board: "자유게시판",
  title: "기록 습관을 어떻게 유지하세요?",
  body: "매일 같은 시간에 기록하는 팁이 궁금해요.",
  createdAt: "방금",
});

assert.equal(newPost.board, "자유게시판");
assert.equal(newPost.comments, 0);
assert.equal(newPost.likes, 0);
assert.deepEqual(newPost.feeds, ["최신글"]);

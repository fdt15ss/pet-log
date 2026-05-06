import type { CommunityBoard, CommunityComment, CommunityFeed, CommunityPost } from "./types";

type CommunityPostQuery = {
  feed: CommunityFeed;
  board: CommunityBoard | null;
};

type CreateCommunityCommentInput = {
  postId: string;
  body: string;
  createdAt?: string;
};

type CreateCommunityPostInput = {
  board: CommunityBoard;
  title: string;
  body: string;
  createdAt?: string;
};

export function getCommunityPosts(posts: CommunityPost[], query: CommunityPostQuery) {
  return posts.filter((post) => {
    const matchesFeed = post.feeds.includes(query.feed);
    const matchesBoard = query.board ? post.board === query.board : true;
    return matchesFeed && matchesBoard;
  });
}

export function getCommunityPostDetail(post: CommunityPost, comments: CommunityComment[]) {
  const commentItems = comments.filter((comment) => comment.postId === post.id);
  const distanceLabel = post.distance ? ` · ${post.distance}` : "";

  return {
    ...post,
    commentItems,
    meta: `${post.board} · 댓글 ${post.comments} · 공감 ${post.likes}${distanceLabel}`,
  };
}

export function createCommunityComment({ postId, body, createdAt = "방금" }: CreateCommunityCommentInput): CommunityComment {
  return {
    id: `comment-${postId}-${Date.now()}`,
    postId,
    authorName: "나",
    body: body.trim(),
    createdAt,
  };
}

export function createCommunityPost({ board, title, body, createdAt = "방금" }: CreateCommunityPostInput): CommunityPost {
  const id = `community-${Date.now()}`;

  return {
    id,
    board,
    title: title.trim(),
    body: body.trim(),
    authorName: "나",
    createdAt,
    comments: 0,
    likes: 0,
    feeds: ["최신글"],
    tags: ["새 글"],
  };
}

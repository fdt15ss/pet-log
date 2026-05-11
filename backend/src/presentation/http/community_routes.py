from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from domain.enums import CommunityBoard, CommunityFeed
from infrastructure.repositories.community_repository import CommunityRepository
from presentation.http.schemas import (
    CommunityCommentRequest,
    CommunityPostRequest,
    CommunityReactionRequest,
    community_comment_to_dict,
    community_post_to_dict,
    success_response,
)


def build_community_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/community")

    @router.get("/posts")
    def list_community_posts(
        http_request: Request,
        feed: CommunityFeed | None = None,
        board: CommunityBoard | None = None,
    ) -> dict[str, object]:
        repository = _community_repository(http_request)
        return success_response(
            {
                "posts": [
                    community_post_to_dict(post)
                    for post in repository.list_posts(feed=feed, board=board)
                ]
            }
        )

    @router.get("/posts/{post_id}")
    def get_community_post(http_request: Request, post_id: str) -> dict[str, object]:
        repository = _community_repository(http_request)
        try:
            post = repository.get_post(post_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Community post not found") from exc

        comments = repository.list_comments(post_id)
        return success_response(
            {
                "post": community_post_to_dict(post),
                "comments": [community_comment_to_dict(comment) for comment in comments],
            }
        )

    @router.post("/posts", status_code=201)
    def create_community_post(
        http_request: Request,
        request: CommunityPostRequest,
    ) -> dict[str, object]:
        repository = _community_repository(http_request)
        post = repository.create_post(
            board=request.board,
            title=request.title,
            body=request.body,
            author_name=request.author_name,
            distance=request.distance,
            tags=tuple(request.tags),
        )
        return success_response({"post": community_post_to_dict(post)})

    @router.post("/posts/{post_id}/comments", status_code=201)
    def create_community_comment(
        http_request: Request,
        post_id: str,
        request: CommunityCommentRequest,
    ) -> dict[str, object]:
        repository = _community_repository(http_request)
        try:
            comment = repository.add_comment(
                post_id=post_id,
                body=request.body,
                author_name=request.author_name,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Community post not found") from exc

        return success_response({"comment": community_comment_to_dict(comment)})

    @router.post("/posts/{post_id}/reactions")
    def create_community_reaction(
        http_request: Request,
        post_id: str,
        request: CommunityReactionRequest,
    ) -> dict[str, object]:
        repository = _community_repository(http_request)
        try:
            repository.add_reaction(post_id=post_id, reaction_type=request.reaction_type)
            post = repository.get_post(post_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Community post not found") from exc

        return success_response({"post": community_post_to_dict(post)})

    return router


def _community_repository(request: Request) -> CommunityRepository:
    repository = getattr(request.app.state.app_context, "community_repository", None)
    if repository is None:
        raise HTTPException(status_code=500, detail="Community repository is not configured")
    return repository

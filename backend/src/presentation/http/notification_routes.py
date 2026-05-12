from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from composition import AppContext
from domain.models import Notification
from presentation.http.schemas import success_response


def build_notification_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/v1/notifications")
    def list_notifications(http_request: Request, pet_id: str) -> dict[str, object]:
        app_context = _app_context(http_request)
        if app_context.notification_repository is None:
            raise HTTPException(status_code=500, detail="Notification repository not configured")
        notifications = app_context.notification_repository.list_for_pet(pet_id)
        return success_response({
            "notifications": [notification_to_frontend(n) for n in notifications]
        })

    @router.patch("/api/v1/notifications/{notification_id}/read")
    def mark_notification_as_read(http_request: Request, notification_id: str) -> dict[str, object]:
        app_context = _app_context(http_request)
        if app_context.notification_repository is None:
            raise HTTPException(status_code=500, detail="Notification repository not configured")
        marked = app_context.notification_repository.mark_as_read(notification_id)
        if not marked:
            raise HTTPException(status_code=404, detail="Notification not found or already read")
        return success_response({"id": notification_id})

    @router.put("/api/v1/notifications/read")
    def mark_all_notifications_as_read(http_request: Request, pet_id: str) -> dict[str, object]:
        app_context = _app_context(http_request)
        if app_context.notification_repository is None:
            raise HTTPException(status_code=500, detail="Notification repository not configured")
        count = app_context.notification_repository.mark_all_as_read(pet_id)
        return success_response({"marked_count": count})

    return router


def _app_context(request: Request) -> AppContext:
    return request.app.state.app_context


def notification_to_frontend(n: Notification) -> dict[str, object]:
    return {
        "id": n.id,
        "category": n.category,
        "title": n.title,
        "detail": n.detail,
        "action": n.action,
        "actionHref": n.action_href,
        "dueLabel": n.due_label,
        "tone": n.tone,
        "createdAt": n.created_at,
        "isRead": n.read_at is not None,
    }

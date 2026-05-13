from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from application.dto import NotificationCandidate
from composition import AppContext
from presentation.http.schemas import success_response

_KIND_CATEGORY = {
    "risk": "주의",
    "behavior_change": "행동 변화",
    "missing_record": "기록",
    "schedule": "일정",
}

_KIND_TONE = {
    "risk": "red",
    "behavior_change": "orange",
    "missing_record": "orange",
    "schedule": "blue",
}

_KIND_ACTION = {
    "risk": "기록 확인",
    "behavior_change": "기록 확인",
    "missing_record": "기록 추가",
    "schedule": "일정 확인",
}

_KIND_HREF = {
    "risk": "/records",
    "behavior_change": "/records",
    "missing_record": "/records/new",
    "schedule": "/schedules",
}


class _MarkReadBody(BaseModel):
    readNotificationIds: list[str]


def build_notification_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/v1/notifications")
    def list_notifications(http_request: Request, pet_id: str) -> dict[str, object]:
        app_context = _app_context(http_request)
        if app_context.notification_repository is None:
            raise HTTPException(status_code=500, detail="Notification repository not configured")

        read_ids = set(app_context.notification_repository.get_read_ids(pet_id))
        candidates = _compute_candidates(app_context, pet_id)

        for c in candidates:
            if c.kind == "missing_record":
                app_context.notification_repository.upsert_from_candidate(
                    pet_id=pet_id,
                    candidate=c,
                    category=_KIND_CATEGORY[c.kind],
                    action=_KIND_ACTION[c.kind],
                    action_href=_KIND_HREF[c.kind],
                    tone=_KIND_TONE[c.kind],
                )

        stored_notifications = (
            app_context.notification_repository.list_for_pet(pet_id)
            if not candidates
            else ()
        )

        return success_response({
            "notifications": [
                *[_candidate_to_frontend(c, read_ids) for c in candidates],
                *[_notification_to_frontend(n, read_ids) for n in stored_notifications],
            ],
            "readNotificationIds": list(read_ids),
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
    def update_read_notifications(
        http_request: Request,
        pet_id: str,
        body: _MarkReadBody | None = None,
    ) -> dict[str, object]:
        app_context = _app_context(http_request)
        if app_context.notification_repository is None:
            raise HTTPException(status_code=500, detail="Notification repository not configured")
        if body is None:
            app_context.notification_repository.mark_all_as_read(pet_id)
            return success_response({"readNotificationIds": list(app_context.notification_repository.get_read_ids(pet_id))})

        ids = tuple(body.readNotificationIds)
        app_context.notification_repository.set_read_ids(pet_id, ids)
        return success_response({"readNotificationIds": list(ids)})

    return router


def _app_context(request: Request) -> AppContext:
    return request.app.state.app_context


def _compute_candidates(app_context: AppContext, pet_id: str) -> tuple[NotificationCandidate, ...]:
    if app_context.context_analysis_agent is None or app_context.notification_policy is None:
        return ()
    if app_context.record_reader is None or app_context.schedule_reader is None:
        return ()

    try:
        pet = app_context.pet_profile_reader.get_pet(pet_id)
    except Exception:
        return ()

    records = app_context.record_reader.list_recent(pet_id, lookback_days=30)
    due_items = app_context.schedule_reader.list_due_items(pet_id, days_ahead=7)

    context = app_context.context_analysis_agent.analyze(pet, records, due_items)
    return app_context.notification_policy.plan(pet, context, safety_notices=(), due_items=due_items)


def _candidate_to_frontend(c: NotificationCandidate, read_ids: set[str]) -> dict[str, object]:
    return {
        "id": c.dedupe_key,
        "category": _KIND_CATEGORY[c.kind],
        "title": c.title,
        "detail": c.message,
        "action": _KIND_ACTION[c.kind],
        "actionHref": _KIND_HREF[c.kind],
        "dueLabel": c.due_date or "",
        "tone": _KIND_TONE[c.kind],
        "isRead": c.dedupe_key in read_ids,
    }


def _notification_to_frontend(notification, read_ids: set[str]) -> dict[str, object]:
    return {
        "id": notification.id,
        "category": notification.category,
        "title": notification.title,
        "detail": notification.detail,
        "action": notification.action,
        "actionHref": notification.action_href,
        "dueLabel": notification.due_label,
        "tone": notification.tone,
        "isRead": bool(notification.read_at) or notification.id in read_ids,
    }

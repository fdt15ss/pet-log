import { strict as assert } from "node:assert";
import test from "node:test";
import {
  buildNotificationSpeechText,
  getNewUnreadNotificationsForSpeech,
  notificationTtsStorageKey,
} from "./notification-tts";
import type { CareNotification } from "./types";

function notification(input: Partial<CareNotification> & Pick<CareNotification, "id">): CareNotification {
  return {
    id: input.id,
    category: input.category ?? "주의",
    title: input.title ?? "주의 기록 후속 확인이 필요합니다",
    detail: input.detail ?? "같은 변화가 이어지는지 오늘 한 번 더 확인해보세요.",
    action: input.action ?? "타임라인 보기",
    actionHref: input.actionHref ?? "/timeline",
    dueLabel: input.dueLabel ?? "오늘",
    tone: input.tone ?? "red",
    createdAt: input.createdAt ?? "2026-05-13T09:30:00",
    isRead: input.isRead ?? false,
  };
}

test("notification TTS text joins title and detail", () => {
  assert.equal(
    buildNotificationSpeechText(notification({ id: "alert-1", title: "  새 알림  ", detail: "  확인해주세요.  " })),
    "새 알림. 확인해주세요.",
  );
});

test("notification TTS skips initial loaded unread notifications", () => {
  const items = [notification({ id: "alert-1" })];

  assert.deepEqual(
    getNewUnreadNotificationsForSpeech({
      hasCompletedInitialLoad: false,
      knownNotificationIds: [],
      notifications: items,
      spokenNotificationIds: [],
    }),
    [],
  );
});

test("notification TTS selects only new unread and unspoken notifications in latest order", () => {
  const selected = getNewUnreadNotificationsForSpeech({
    hasCompletedInitialLoad: true,
    knownNotificationIds: ["known-unread"],
    notifications: [
      notification({ id: "known-unread", createdAt: "2026-05-13T09:30:00" }),
      notification({ id: "new-read", createdAt: "2026-05-13T09:40:00", isRead: true }),
      notification({ id: "already-spoken", createdAt: "2026-05-13T09:50:00" }),
      notification({ id: "new-late", createdAt: "2026-05-13T10:00:00" }),
      notification({ id: "new-early", createdAt: "2026-05-13T09:55:00" }),
    ],
    spokenNotificationIds: ["already-spoken"],
  });

  assert.deepEqual(selected.map((item) => item.id), ["new-late", "new-early"]);
});

test("notification TTS storage key is stable", () => {
  assert.equal(notificationTtsStorageKey, "pet-log-notification-tts-spoken-v1");
});

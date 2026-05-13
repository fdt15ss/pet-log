import { sortCareNotificationsByLatest } from "./notifications";
import type { CareNotification } from "./types";

export const notificationTtsStorageKey = "pet-log-notification-tts-spoken-v1";

type NewUnreadNotificationInput = {
  hasCompletedInitialLoad: boolean;
  knownNotificationIds: string[];
  notifications: CareNotification[];
  spokenNotificationIds: string[];
};

export function buildNotificationSpeechText(notification: CareNotification) {
  return `${notification.title.trim()}. ${notification.detail.trim()}`.trim();
}

export function getNewUnreadNotificationsForSpeech({
  hasCompletedInitialLoad,
  knownNotificationIds,
  notifications,
  spokenNotificationIds,
}: NewUnreadNotificationInput) {
  if (!hasCompletedInitialLoad) {
    return [];
  }

  const knownIds = new Set(knownNotificationIds);
  const spokenIds = new Set(spokenNotificationIds);
  return sortCareNotificationsByLatest(notifications).filter(
    (notification) => !notification.isRead && !knownIds.has(notification.id) && !spokenIds.has(notification.id),
  );
}

export function parseSpokenNotificationIds(value: string | null) {
  if (!value) {
    return [];
  }

  try {
    const parsed: unknown = JSON.parse(value);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
  } catch {
    return [];
  }
}

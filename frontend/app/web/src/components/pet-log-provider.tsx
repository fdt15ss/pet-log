"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  createRecord as createRecordApi,
  createSchedule as createScheduleApi,
  deleteRecord as deleteRecordApi,
  deleteSchedule as deleteScheduleApi,
  getPetLogSnapshot,
  resetPetLogSnapshot,
  structureRecordPreview,
  updateExpansionState as updateExpansionStateApi,
  updateProfile as updateProfileApi,
  updateReadNotifications,
  updateRecord as updateRecordApi,
  updateSchedule as updateScheduleApi,
  updateSettings as updateSettingsApi,
  type PetLogSnapshot,
} from "@/lib/api-client";
import { defaultExpansionState, normalizeExpansionState } from "@/lib/expansion-state";
import { petProfile as initialProfile, records as initialRecords, schedules as initialSchedules } from "@/lib/mock-data";
import { defaultAppSettings } from "@/lib/settings";
import type { ExpansionState, HospitalState, SharedCareState, ShoppingState } from "@/lib/expansion-state";
import type { AppSettings, CareSchedule, PetProfile, RecordCategory, RecordEntry, ScheduleCategory, StructuredRecord } from "@/lib/types";

type NewRecordInput = {
  category: RecordCategory;
  detail: string;
};

type UpdateRecordInput = {
  category: RecordCategory;
  detail: string;
};

type NewScheduleInput = {
  category: ScheduleCategory;
  title: string;
  dueDate: string;
  repeatLabel: string;
  note: string;
};

type StoredPetLogState = {
  version: 1;
  profile: PetProfile;
  records: RecordEntry[];
  schedules?: CareSchedule[];
  settings?: AppSettings;
  readNotificationIds?: string[];
  expansionState?: ExpansionState;
};

type PetLogContextValue = {
  profile: PetProfile;
  records: RecordEntry[];
  schedules: CareSchedule[];
  settings: AppSettings;
  readNotificationIds: string[];
  expansionState: ExpansionState;
  isLoading: boolean;
  error: string;
  syncStatus: "idle" | "synced" | "offline" | "error";
  addRecord: (input: NewRecordInput) => Promise<RecordEntry>;
  updateRecord: (id: string, input: UpdateRecordInput) => Promise<void>;
  deleteRecord: (id: string) => Promise<void>;
  updateProfile: (input: PetProfile) => Promise<PetProfile>;
  updateSettings: (input: AppSettings) => Promise<void>;
  updateSharedCareState: (input: Partial<SharedCareState>) => Promise<void>;
  updateHospitalState: (input: Partial<HospitalState>) => Promise<void>;
  updateShoppingState: (input: Partial<ShoppingState>) => Promise<void>;
  resetPetLogData: () => Promise<void>;
  markNotificationRead: (id: string) => Promise<void>;
  markAllNotificationsRead: (ids: string[]) => Promise<void>;
  addSchedule: (input: NewScheduleInput) => Promise<CareSchedule>;
  toggleScheduleDone: (id: string) => Promise<void>;
  deleteSchedule: (id: string) => Promise<void>;
};

const storageKey = "pet-log-state-v1";
const PetLogContext = createContext<PetLogContextValue | null>(null);

function formatDateLabel(date: Date) {
  return `${date.getMonth() + 1}월 ${date.getDate()}일`;
}

function formatTimeLabel(date: Date) {
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function createTitle(detail: string) {
  const firstLine = detail.trim().split(/\n|[.!?。]/)[0]?.trim() ?? "";
  if (firstLine.length <= 24) {
    return firstLine || "새 기록";
  }
  return `${firstLine.slice(0, 24)}...`;
}

function createFallbackStructuredRecord(detail: string, category: RecordCategory): StructuredRecord {
  const sourceText = detail.trim();
  return {
    sourceText,
    normalizedSummary: createTitle(sourceText),
    suggestedCategory: category,
    confidence: 0.4,
    measurements: [],
    needsConfirmation: true,
  };
}

function createLocalRecord(input: NewRecordInput, structured: StructuredRecord, createdAt = new Date()): RecordEntry {
  const detail = input.detail.trim();
  return {
    id: `local-${createdAt.getTime()}`,
    date: formatDateLabel(createdAt),
    time: formatTimeLabel(createdAt),
    category: input.category,
    title: createTitle(detail),
    detail,
    status: "normal",
    structured,
  };
}

function createLocalSchedule(input: NewScheduleInput, createdAt = new Date()): CareSchedule {
  return {
    id: `schedule-${createdAt.getTime()}`,
    category: input.category,
    title: input.title.trim(),
    dueDate: input.dueDate,
    repeatLabel: input.repeatLabel.trim() || "한 번",
    note: input.note.trim(),
    isDone: false,
  };
}

function isRecordCategory(value: unknown): value is RecordCategory {
  return value === "meal" || value === "walk" || value === "stool" || value === "medical" || value === "behavior";
}

function isScheduleCategory(value: unknown): value is ScheduleCategory {
  return value === "vaccination" || value === "medication" || value === "checkup" || value === "grooming" || value === "food";
}

function isRecordEntry(value: unknown): value is RecordEntry {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as RecordEntry;
  return (
    typeof record.id === "string" &&
    typeof record.date === "string" &&
    typeof record.time === "string" &&
    isRecordCategory(record.category) &&
    typeof record.title === "string" &&
    typeof record.detail === "string" &&
    (record.status === "normal" || record.status === "notice" || record.status === "alert")
  );
}

function isCareSchedule(value: unknown): value is CareSchedule {
  if (!value || typeof value !== "object") {
    return false;
  }

  const schedule = value as CareSchedule;
  return (
    typeof schedule.id === "string" &&
    isScheduleCategory(schedule.category) &&
    typeof schedule.title === "string" &&
    typeof schedule.dueDate === "string" &&
    typeof schedule.repeatLabel === "string" &&
    typeof schedule.note === "string" &&
    typeof schedule.isDone === "boolean"
  );
}

function isPetProfile(value: unknown): value is PetProfile {
  if (!value || typeof value !== "object") {
    return false;
  }

  const profile = value as PetProfile;
  return (
    typeof profile.name === "string" &&
    typeof profile.breed === "string" &&
    typeof profile.age === "string" &&
    typeof profile.sex === "string" &&
    typeof profile.weight === "string" &&
    typeof profile.birthday === "string" &&
    typeof profile.personality === "string" &&
    (profile.photoDataUrl === undefined || typeof profile.photoDataUrl === "string") &&
    Array.isArray(profile.notes) &&
    profile.notes.every((note) => typeof note === "string")
  );
}

function isAppSettings(value: unknown): value is AppSettings {
  if (!value || typeof value !== "object") {
    return false;
  }

  const settings = value as AppSettings;
  return (
    typeof settings.aiInsightEnabled === "boolean" &&
    !!settings.notificationPreferences &&
    typeof settings.notificationPreferences.missingRecord === "boolean" &&
    typeof settings.notificationPreferences.alert === "boolean" &&
    typeof settings.notificationPreferences.schedule === "boolean"
  );
}

function parseStoredState(value: string | null): StoredPetLogState | null {
  if (!value) {
    return null;
  }

  try {
    const parsed = JSON.parse(value) as Partial<StoredPetLogState>;
    if (
      parsed.version === 1 &&
      isPetProfile(parsed.profile) &&
      Array.isArray(parsed.records) &&
      parsed.records.every(isRecordEntry) &&
      (parsed.schedules === undefined || (Array.isArray(parsed.schedules) && parsed.schedules.every(isCareSchedule))) &&
      (parsed.settings === undefined || isAppSettings(parsed.settings)) &&
      (parsed.readNotificationIds === undefined ||
        (Array.isArray(parsed.readNotificationIds) && parsed.readNotificationIds.every((id) => typeof id === "string")))
    ) {
      return {
        ...(parsed as StoredPetLogState),
        expansionState: normalizeExpansionState(parsed.expansionState),
      };
    }
  } catch {
    return null;
  }

  return null;
}

export function PetLogProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<PetProfile>(initialProfile);
  const [records, setRecords] = useState<RecordEntry[]>(initialRecords);
  const [schedules, setSchedules] = useState<CareSchedule[]>(initialSchedules);
  const [settings, setSettings] = useState<AppSettings>(defaultAppSettings);
  const [readNotificationIds, setReadNotificationIds] = useState<string[]>([]);
  const [expansionState, setExpansionState] = useState<ExpansionState>(defaultExpansionState);
  const [isStorageReady, setIsStorageReady] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [syncStatus, setSyncStatus] = useState<"idle" | "synced" | "offline" | "error">("idle");

  const applySnapshot = useCallback((snapshot: PetLogSnapshot) => {
    setProfile(snapshot.profile);
    setRecords(snapshot.records);
    setSchedules(snapshot.schedules);
    setSettings(snapshot.settings);
    setReadNotificationIds(snapshot.readNotificationIds);
    setExpansionState(normalizeExpansionState(snapshot.expansionState));
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialState() {
      setIsLoading(true);
      let storedState: StoredPetLogState | null = null;
      try {
        storedState = parseStoredState(window.localStorage.getItem(storageKey));
      } catch {
        storedState = null;
      }

      if (storedState) {
        setProfile(storedState.profile);
        setRecords(storedState.records);
        setSchedules(storedState.schedules ?? initialSchedules);
        setSettings(storedState.settings ?? defaultAppSettings);
        setReadNotificationIds(storedState.readNotificationIds ?? []);
        setExpansionState(storedState.expansionState ?? defaultExpansionState);
      }

      try {
        const snapshot = await getPetLogSnapshot();
        if (cancelled) {
          return;
        }
        applySnapshot(snapshot);
        setError("");
        setSyncStatus("synced");
      } catch {
        if (cancelled) {
          return;
        }
        setError("API 연결에 실패해 로컬 데모 상태를 사용합니다.");
        setSyncStatus("offline");
      } finally {
        if (!cancelled) {
          setIsStorageReady(true);
          setIsLoading(false);
        }
      }
    }

    void loadInitialState();

    return () => {
      cancelled = true;
    };
  }, [applySnapshot]);

  useEffect(() => {
    if (!isStorageReady) {
      return;
    }

    const state: StoredPetLogState = {
      version: 1,
      profile,
      records,
      schedules,
      settings,
      readNotificationIds,
      expansionState,
    };

    try {
      window.localStorage.setItem(storageKey, JSON.stringify(state));
    } catch {
      // 저장소 사용이 막힌 환경에서는 현재 세션 상태만 유지합니다.
    }
  }, [isStorageReady, profile, records, schedules, settings, readNotificationIds, expansionState]);

  const addRecord = useCallback(async (input: NewRecordInput) => {
    try {
      const { record } = await createRecordApi(input);
      setRecords((current) => [record, ...current]);
      setError("");
      setSyncStatus("synced");
      return record;
    } catch {
      const fallbackStructured = await structureRecordPreview({ detail: input.detail, fallbackCategory: input.category })
        .then((response) => response.structured)
        .catch(() => createFallbackStructuredRecord(input.detail, input.category));
      const fallbackRecord = createLocalRecord(input, fallbackStructured);
      setRecords((current) => [fallbackRecord, ...current]);
      setError("API 저장에 실패해 로컬 기록으로 유지했습니다.");
      setSyncStatus("offline");
      return fallbackRecord;
    }
  }, []);

  const updateRecord = useCallback(async (id: string, input: UpdateRecordInput) => {
    try {
      const { record } = await updateRecordApi(id, input);
      setRecords((current) => current.map((item) => (item.id === id ? record : item)));
      setError("");
      setSyncStatus("synced");
    } catch {
      setError("API 수정에 실패해 이전 기록으로 되돌렸습니다.");
      setSyncStatus("offline");
    }
  }, []);

  const deleteRecord = useCallback(async (id: string) => {
    const previousRecords = records;
    setRecords((current) => current.filter((record) => record.id !== id));

    try {
      await deleteRecordApi(id);
      setError("");
      setSyncStatus("synced");
    } catch {
      setRecords(previousRecords);
      setError("API 삭제에 실패해 이전 기록으로 되돌렸습니다.");
      setSyncStatus("offline");
    }
  }, [records]);

  const updateProfile = useCallback(async (input: PetProfile) => {
    const nextProfile = {
      ...input,
      notes: input.notes.map((note) => note.trim()).filter(Boolean),
      photoDataUrl: input.photoDataUrl || undefined,
    };
    const previousProfile = profile;
    setProfile(nextProfile);

    try {
      const { profile } = await updateProfileApi(nextProfile);
      setProfile(profile);
      setError("");
      setSyncStatus("synced");
      return profile;
    } catch {
      setProfile(previousProfile);
      setError("API 프로필 저장에 실패했습니다.");
      setSyncStatus("offline");
      return previousProfile;
    }
  }, [profile]);

  const updateSettings = useCallback(async (input: AppSettings) => {
    const nextSettings = {
      notificationPreferences: {
        missingRecord: input.notificationPreferences.missingRecord,
        alert: input.notificationPreferences.alert,
        schedule: input.notificationPreferences.schedule,
      },
      aiInsightEnabled: input.aiInsightEnabled,
    };
    const previousSettings = settings;
    setSettings(nextSettings);

    try {
      const { settings } = await updateSettingsApi(nextSettings);
      setSettings(settings);
      setError("");
      setSyncStatus("synced");
    } catch {
      setSettings(previousSettings);
      setError("API 설정 저장에 실패했습니다.");
      setSyncStatus("offline");
    }
  }, [settings]);

  const persistExpansionState = useCallback(async (nextState: ExpansionState, previousState: ExpansionState) => {
    try {
      const { expansionState } = await updateExpansionStateApi(nextState);
      setExpansionState(expansionState);
      setError("");
      setSyncStatus("synced");
    } catch {
      setExpansionState(previousState);
      setError("API 확장 상태 저장에 실패했습니다.");
      setSyncStatus("offline");
    }
  }, []);

  const updateSharedCareState = useCallback(async (input: Partial<SharedCareState>) => {
    const previousState = expansionState;
    const nextState = normalizeExpansionState({
      ...expansionState,
      sharedCare: {
        ...expansionState.sharedCare,
        ...input,
      },
    });
    setExpansionState(nextState);
    await persistExpansionState(nextState, previousState);
  }, [expansionState, persistExpansionState]);

  const updateHospitalState = useCallback(async (input: Partial<HospitalState>) => {
    const previousState = expansionState;
    const nextState = normalizeExpansionState({
      ...expansionState,
      hospital: {
        ...expansionState.hospital,
        ...input,
      },
    });
    setExpansionState(nextState);
    await persistExpansionState(nextState, previousState);
  }, [expansionState, persistExpansionState]);

  const updateShoppingState = useCallback(async (input: Partial<ShoppingState>) => {
    const previousState = expansionState;
    const nextState = normalizeExpansionState({
      ...expansionState,
      shopping: {
        ...expansionState.shopping,
        ...input,
      },
    });
    setExpansionState(nextState);
    await persistExpansionState(nextState, previousState);
  }, [expansionState, persistExpansionState]);

  const resetPetLogData = useCallback(async () => {
    try {
      const snapshot = await resetPetLogSnapshot();
      applySnapshot(snapshot);
      setError("");
      setSyncStatus("synced");
    } catch {
      setProfile(initialProfile);
      setRecords(initialRecords);
      setSchedules(initialSchedules);
      setSettings(defaultAppSettings);
      setReadNotificationIds([]);
      setExpansionState(defaultExpansionState);
      setError("API 초기화에 실패해 로컬 예시 데이터로 되돌렸습니다.");
      setSyncStatus("offline");
    }
  }, [applySnapshot]);

  const persistReadNotificationIds = useCallback(async (ids: string[]) => {
    try {
      const response = await updateReadNotifications(ids);
      setReadNotificationIds(response.readNotificationIds);
      setError("");
      setSyncStatus("synced");
    } catch {
      setError("API 알림 읽음 저장에 실패했습니다.");
      setSyncStatus("offline");
    }
  }, []);

  const markNotificationRead = useCallback(async (id: string) => {
    const nextIds = readNotificationIds.includes(id) ? readNotificationIds : [...readNotificationIds, id];
    setReadNotificationIds(nextIds);
    await persistReadNotificationIds(nextIds);
  }, [persistReadNotificationIds, readNotificationIds]);

  const markAllNotificationsRead = useCallback(async (ids: string[]) => {
    const nextIds = Array.from(new Set([...readNotificationIds, ...ids]));
    setReadNotificationIds(nextIds);
    await persistReadNotificationIds(nextIds);
  }, [persistReadNotificationIds, readNotificationIds]);

  const addSchedule = useCallback(async (input: NewScheduleInput) => {
    const fallbackSchedule = createLocalSchedule(input);
    setSchedules((current) => [fallbackSchedule, ...current]);

    try {
      const { schedule } = await createScheduleApi(input);
      setSchedules((current) => current.map((item) => (item.id === fallbackSchedule.id ? schedule : item)));
      setError("");
      setSyncStatus("synced");
      return schedule;
    } catch {
      setError("API 일정 저장에 실패해 로컬 일정으로 유지했습니다.");
      setSyncStatus("offline");
      return fallbackSchedule;
    }
  }, []);

  const toggleScheduleDone = useCallback(async (id: string) => {
    const targetSchedule = schedules.find((schedule) => schedule.id === id);
    if (!targetSchedule) {
      return;
    }

    const previousSchedules = schedules;
    const nextDone = !targetSchedule.isDone;
    setSchedules((current) => current.map((schedule) => (schedule.id === id ? { ...schedule, isDone: nextDone } : schedule)));

    try {
      const { schedule } = await updateScheduleApi(id, { isDone: nextDone });
      setSchedules((current) => current.map((item) => (item.id === id ? schedule : item)));
      setError("");
      setSyncStatus("synced");
    } catch {
      setSchedules(previousSchedules);
      setError("API 일정 수정에 실패했습니다.");
      setSyncStatus("offline");
    }
  }, [schedules]);

  const deleteSchedule = useCallback(async (id: string) => {
    const previousSchedules = schedules;
    setSchedules((current) => current.filter((schedule) => schedule.id !== id));

    try {
      await deleteScheduleApi(id);
      setError("");
      setSyncStatus("synced");
    } catch {
      setSchedules(previousSchedules);
      setError("API 일정 삭제에 실패했습니다.");
      setSyncStatus("offline");
    }
  }, [schedules]);

  const value = useMemo(
    () => ({
      profile,
      records,
      schedules,
      settings,
      readNotificationIds,
      expansionState,
      isLoading,
      error,
      syncStatus,
      addRecord,
      updateRecord,
      deleteRecord,
      updateProfile,
      updateSettings,
      updateSharedCareState,
      updateHospitalState,
      updateShoppingState,
      resetPetLogData,
      markNotificationRead,
      markAllNotificationsRead,
      addSchedule,
      toggleScheduleDone,
      deleteSchedule,
    }),
    [
      profile,
      records,
      schedules,
      settings,
      readNotificationIds,
      expansionState,
      isLoading,
      error,
      syncStatus,
      addRecord,
      updateRecord,
      deleteRecord,
      updateProfile,
      updateSettings,
      updateSharedCareState,
      updateHospitalState,
      updateShoppingState,
      resetPetLogData,
      markNotificationRead,
      markAllNotificationsRead,
      addSchedule,
      toggleScheduleDone,
      deleteSchedule,
    ],
  );

  return <PetLogContext.Provider value={value}>{children}</PetLogContext.Provider>;
}

export function usePetLog() {
  const context = useContext(PetLogContext);
  if (!context) {
    throw new Error("usePetLog must be used within PetLogProvider");
  }
  return context;
}

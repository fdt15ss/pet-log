"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  createRecord as createRecordApi,
  createSchedule as createScheduleApi,
  deleteRecord as deleteRecordApi,
  deleteSchedule as deleteScheduleApi,
  fetchAiInsights,
  fetchAiSuggestions,
  fetchMe,
  fetchNotifications,
  fetchPets,
  fetchRecords,
  fetchSchedules,
  structureRecordPreview,
  type CreateRecordResponse,
  updateExpansionState as updateExpansionStateApi,
  updateProfile as updateProfileApi,
  updateReadNotifications,
  updateRecord as updateRecordApi,
  updateSchedule as updateScheduleApi,
  updateSettings as updateSettingsApi,
} from "@/lib/api-client";
import {
  defaultExpansionState,
  normalizeExpansionState,
} from "@/lib/expansion-state";
import {
  buildConfirmedRecordCandidates,
  structuredFromCandidate,
} from "@/lib/record-candidates";
import { defaultAppSettings } from "@/lib/settings";
import type {
  ExpansionState,
  HospitalState,
  SharedCareState,
  ShoppingState,
} from "@/lib/expansion-state";
import type {
  AiInsight,
  AiSuggestion,
  AppSettings,
  CareSchedule,
  PetProfile,
  RecordCategory,
  RecordCategoryChoice,
  RecordEntry,
  ScheduleCategory,
  StructuredRecord,
  StructuredRecordCandidate,
} from "@/lib/types";

type PetNotification = {
  id: string;
  isRead: boolean;
};

type NewRecordInput = {
  category: RecordCategoryChoice;
  detail: string;
  structured?: StructuredRecord;
  candidates?: StructuredRecordCandidate[];
  source?: "manual" | "voice" | "ai_preview";
};

type UpdateRecordInput = {
  category: RecordCategoryChoice;
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
  insights: AiInsight[];
  suggestions: AiSuggestion[];
  isLoading: boolean;
  isAnalysisLoading: boolean;
  error: string;
  syncStatus: "idle" | "synced" | "offline" | "error";
  addRecord: (input: NewRecordInput) => Promise<CreateRecordResponse>;
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
  refreshAnalysis: (petId: string) => Promise<void>;
};

const storageKey = "pet-log-state-v1";
const PetLogContext = createContext<PetLogContextValue | null>(null);

const emptyProfile: PetProfile = {
  name: "",
  breed: "",
  age: "",
  sex: "",
  weight: "",
  birthday: "",
  personality: "",
  notes: [],
};

function activePetId(profile: PetProfile): string {
  const value = (profile as PetProfile & { id?: unknown }).id;
  return typeof value === "string" ? value : "";
}

function normalizeRecordCategory(
  category: RecordCategoryChoice,
): RecordCategory {
  return category === "all" ? "meal" : category;
}

function dateLabel(value = new Date()): string {
  return `${value.getMonth() + 1}월 ${value.getDate()}일`;
}

function timeLabel(value = new Date()): string {
  return `${String(value.getHours()).padStart(2, "0")}:${String(
    value.getMinutes(),
  ).padStart(2, "0")}`;
}

function createFallbackStructuredRecord(
  detail: string,
  fallbackCategory: RecordCategory,
): StructuredRecord {
  return {
    sourceText: detail,
    normalizedSummary: detail.trim().slice(0, 80) || "새 기록",
    suggestedCategory: fallbackCategory,
    detectedCategories: [fallbackCategory],
    confidence: 0.5,
    measurements: [],
    needsConfirmation: false,
  };
}

function createLocalRecord(
  input: NewRecordInput,
  structured: StructuredRecord,
): RecordEntry {
  const now = new Date();
  const category = normalizeRecordCategory(input.category);

  return {
    id: `local-record-${now.getTime()}-${Math.random()
      .toString(36)
      .slice(2, 8)}`,
    date: dateLabel(now),
    time: timeLabel(now),
    category,
    categoryChoice: input.category,
    title:
      structured.normalizedSummary ||
      input.detail.trim().slice(0, 80) ||
      "새 기록",
    detail: input.detail,
    status: "normal",
    structured,
  };
}

function createLocalSchedule(
  input: NewScheduleInput,
  createdAt = new Date(),
): CareSchedule {
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

export function PetLogProvider({ children }: { children: ReactNode }) {
  console.log("[provider] 초기화 시작 → 클라이언트 fetch 예정");

  const [profile, setProfile] = useState<PetProfile>(emptyProfile);
  const [records, setRecords] = useState<RecordEntry[]>([]);
  const [schedules, setSchedules] = useState<CareSchedule[]>([]);
  const [settings, setSettings] = useState<AppSettings>(defaultAppSettings);
  const [readNotificationIds, setReadNotificationIds] = useState<string[]>([]);
  const [expansionState, setExpansionState] = useState<ExpansionState>(
    normalizeExpansionState(undefined),
  );
  const [insights, setInsights] = useState<AiInsight[]>([]);
  const [suggestions, setSuggestions] = useState<AiSuggestion[]>([]);
  const [isStorageReady, setIsStorageReady] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
  const [error, setError] = useState(
    "API 연결에 실패했습니다. 서버 연결을 확인해주세요.",
  );
  const [syncStatus, setSyncStatus] = useState<
    "idle" | "synced" | "offline" | "error"
  >("error");

  const refreshAnalysis = useCallback(async (petId: string) => {
    if (!petId) {
      return;
    }

    setIsAnalysisLoading(true);

    try {
      const [insightsResult, suggestionsResult] = await Promise.allSettled([
        fetchAiInsights(petId),
        fetchAiSuggestions(petId),
      ]);

      if (insightsResult.status === "fulfilled") {
        setInsights(insightsResult.value.insights);
      } else {
        console.log(
          "[provider] AI 인사이트 갱신 실패:",
          insightsResult.reason instanceof Error
            ? insightsResult.reason.message
            : insightsResult.reason,
        );
        setInsights([]);
      }

      if (suggestionsResult.status === "fulfilled") {
        setSuggestions(suggestionsResult.value.suggestions);
      } else {
        console.log(
          "[provider] AI 케어 제안 갱신 실패:",
          suggestionsResult.reason instanceof Error
            ? suggestionsResult.reason.message
            : suggestionsResult.reason,
        );
        setSuggestions([]);
      }
    } finally {
      setIsAnalysisLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialState() {
      setIsLoading(true);

      try {
        console.log("[provider] 개별 API 병렬 로딩 시작");

        const [, { pets }] = await Promise.all([fetchMe(), fetchPets()]);

        if (cancelled) {
          return;
        }

        const activePet = pets[0];
        if (!activePet) {
          console.log(
            "[provider] 등록된 반려동물이 없어 빈 상태로 시작합니다.",
          );
          setProfile(emptyProfile);
          setRecords([]);
          setSchedules([]);
          setSettings(defaultAppSettings);
          setReadNotificationIds([]);
          setExpansionState(defaultExpansionState);
          setInsights([]);
          setSuggestions([]);
          setError("반려동물을 등록하면 기록을 시작할 수 있습니다.");
          setSyncStatus("synced");
          setIsStorageReady(true);
          setIsLoading(false);
          return;
        }

        const [recordsData, schedulesData, notificationsData] =
          await Promise.all([
            fetchRecords(activePet.id),
            fetchSchedules(activePet.id),
            fetchNotifications(activePet.id),
          ]);

        if (cancelled) {
          return;
        }

        console.log(
          `[provider] 로딩 완료: pet=${activePet.name}, records=${recordsData.records.length}, schedules=${schedulesData.schedules.length}`,
        );

        setProfile(activePet);
        setRecords(recordsData.records);
        setSchedules(schedulesData.schedules);
        setSettings(defaultAppSettings);
        setReadNotificationIds(
          (notificationsData.notifications as PetNotification[])
            .filter((notification) => notification.isRead)
            .map((notification) => notification.id),
        );
        setExpansionState(defaultExpansionState);

        void refreshAnalysis(activePet.id);

        setError("");
        setSyncStatus("synced");
        setIsStorageReady(true);
        setIsLoading(false);
      } catch (err) {
        console.error("[provider] 로딩 실패:", err);
        if (cancelled) {
          return;
        }

        setError("데이터를 불러오지 못했습니다. 서버 연결을 확인해주세요.");
        setSyncStatus("error");
        setIsLoading(false);
      }
    }

    void loadInitialState().catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [refreshAnalysis]);

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
  }, [
    isStorageReady,
    profile,
    records,
    schedules,
    settings,
    readNotificationIds,
    expansionState,
  ]);

  const addRecord = useCallback(
    async (input: NewRecordInput) => {
      try {
        const response = await createRecordApi(input);
        setRecords((current) => [...response.records, ...current]);

        const petId = activePetId(profile);
        if (petId) {
          void refreshAnalysis(petId);
        }

        setError("");
        setSyncStatus(response.storage === "backend" ? "synced" : "offline");
        return response;
      } catch {
        const fallbackStructured = await structureRecordPreview({
          detail: input.detail,
          fallbackCategory: input.category,
        })
          .then((response) => response.structured)
          .catch(() =>
            createFallbackStructuredRecord(
              input.detail,
              normalizeRecordCategory(input.category),
            ),
          );

        const fallbackCandidates = input.candidates?.length
          ? input.candidates
          : buildConfirmedRecordCandidates(fallbackStructured);

        const fallbackRecords = fallbackCandidates.map((candidate) =>
          createLocalRecord(
            input,
            structuredFromCandidate(candidate, input.detail),
          ),
        );

        setRecords((current) => [...fallbackRecords, ...current]);
        setError("API 저장에 실패해 로컬 기록으로 유지했습니다.");
        setSyncStatus("offline");

        return {
          record: fallbackRecords[0],
          records: fallbackRecords,
          storage: "local" as const,
          storageMessage:
            "API 저장에 실패해 브라우저 로컬 상태에 저장했습니다.",
        };
      }
    },
    [profile, refreshAnalysis],
  );

  const updateRecord = useCallback(
    async (id: string, input: UpdateRecordInput) => {
      try {
        const { record } = await updateRecordApi(id, input);
        setRecords((current) =>
          current.map((item) => (item.id === id ? record : item)),
        );

        const petId = activePetId(profile);
        if (petId) {
          void refreshAnalysis(petId);
        }

        setError("");
        setSyncStatus("synced");
      } catch {
        setError("API 수정에 실패해 이전 기록으로 되돌렸습니다.");
        setSyncStatus("offline");
      }
    },
    [profile, refreshAnalysis],
  );

  const deleteRecord = useCallback(
    async (id: string) => {
      const previousRecords = records;
      setRecords((current) => current.filter((record) => record.id !== id));

      try {
        await deleteRecordApi(id);

        const petId = activePetId(profile);
        if (petId) {
          void refreshAnalysis(petId);
        }

        setError("");
        setSyncStatus("synced");
      } catch {
        setRecords(previousRecords);
        setError("API 삭제에 실패해 이전 기록으로 되돌렸습니다.");
        setSyncStatus("offline");
      }
    },
    [profile, records, refreshAnalysis],
  );

  const updateProfile = useCallback(
    async (input: PetProfile) => {
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
    },
    [profile],
  );

  const updateSettings = useCallback(
    async (input: AppSettings) => {
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
    },
    [settings],
  );

  const persistExpansionState = useCallback(
    async (nextState: ExpansionState, previousState: ExpansionState) => {
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
    },
    [],
  );

  const updateSharedCareState = useCallback(
    async (input: Partial<SharedCareState>) => {
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
    },
    [expansionState, persistExpansionState],
  );

  const updateHospitalState = useCallback(
    async (input: Partial<HospitalState>) => {
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
    },
    [expansionState, persistExpansionState],
  );

  const updateShoppingState = useCallback(
    async (input: Partial<ShoppingState>) => {
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
    },
    [expansionState, persistExpansionState],
  );

  const resetPetLogData = useCallback(async () => {
    try {
      console.log("[provider] 데이터 리로딩 시작");

      const [, { pets }] = await Promise.all([fetchMe(), fetchPets()]);
      const activePet = pets[0];

      if (activePet) {
        const [recordsData, schedulesData, notificationsData] =
          await Promise.all([
            fetchRecords(activePet.id),
            fetchSchedules(activePet.id),
            fetchNotifications(activePet.id),
          ]);

        setProfile(activePet);
        setRecords(recordsData.records);
        setSchedules(schedulesData.schedules);
        setReadNotificationIds(
          (notificationsData.notifications as PetNotification[])
            .filter((notification) => notification.isRead)
            .map((notification) => notification.id),
        );

        void refreshAnalysis(activePet.id);
      } else {
        setProfile(emptyProfile);
        setRecords([]);
        setSchedules([]);
        setReadNotificationIds([]);
        setInsights([]);
        setSuggestions([]);
      }

      setError("");
      setSyncStatus("synced");
    } catch {
      setError("데이터 초기화에 실패했습니다. 서버 연결을 확인해주세요.");
      setSyncStatus("error");
    }
  }, [refreshAnalysis]);

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

  const markNotificationRead = useCallback(
    async (id: string) => {
      const nextIds = readNotificationIds.includes(id)
        ? readNotificationIds
        : [...readNotificationIds, id];
      setReadNotificationIds(nextIds);
      await persistReadNotificationIds(nextIds);
    },
    [persistReadNotificationIds, readNotificationIds],
  );

  const markAllNotificationsRead = useCallback(
    async (ids: string[]) => {
      const nextIds = Array.from(new Set([...readNotificationIds, ...ids]));
      setReadNotificationIds(nextIds);
      await persistReadNotificationIds(nextIds);
    },
    [persistReadNotificationIds, readNotificationIds],
  );

  const addSchedule = useCallback(async (input: NewScheduleInput) => {
    const fallbackSchedule = createLocalSchedule(input);
    setSchedules((current) => [fallbackSchedule, ...current]);

    try {
      const { schedule } = await createScheduleApi(input);
      setSchedules((current) =>
        current.map((item) =>
          item.id === fallbackSchedule.id ? schedule : item,
        ),
      );
      setError("");
      setSyncStatus("synced");
      return schedule;
    } catch {
      setError("API 일정 저장에 실패해 로컬 일정으로 유지했습니다.");
      setSyncStatus("offline");
      return fallbackSchedule;
    }
  }, []);

  const toggleScheduleDone = useCallback(
    async (id: string) => {
      const targetSchedule = schedules.find((schedule) => schedule.id === id);
      if (!targetSchedule) {
        return;
      }

      const previousSchedules = schedules;
      const nextDone = !targetSchedule.isDone;
      setSchedules((current) =>
        current.map((schedule) =>
          schedule.id === id ? { ...schedule, isDone: nextDone } : schedule,
        ),
      );

      try {
        const { schedule } = await updateScheduleApi(id, { isDone: nextDone });
        setSchedules((current) =>
          current.map((item) => (item.id === id ? schedule : item)),
        );
        setError("");
        setSyncStatus("synced");
      } catch {
        setSchedules(previousSchedules);
        setError("API 일정 수정에 실패했습니다.");
        setSyncStatus("offline");
      }
    },
    [schedules],
  );

  const deleteSchedule = useCallback(
    async (id: string) => {
      const previousSchedules = schedules;
      setSchedules((current) =>
        current.filter((schedule) => schedule.id !== id),
      );

      try {
        await deleteScheduleApi(id);
        setError("");
        setSyncStatus("synced");
      } catch {
        setSchedules(previousSchedules);
        setError("API 일정 삭제에 실패했습니다.");
        setSyncStatus("offline");
      }
    },
    [schedules],
  );

  const value = useMemo(
    () => ({
      profile,
      records,
      schedules,
      settings,
      readNotificationIds,
      expansionState,
      insights,
      suggestions,
      isLoading,
      isAnalysisLoading,
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
      refreshAnalysis,
    }),
    [
      profile,
      records,
      schedules,
      settings,
      readNotificationIds,
      expansionState,
      insights,
      suggestions,
      isLoading,
      isAnalysisLoading,
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
      refreshAnalysis,
    ],
  );

  return (
    <PetLogContext.Provider value={value}>{children}</PetLogContext.Provider>
  );
}

export function usePetLog() {
  const context = useContext(PetLogContext);
  if (!context) {
    throw new Error("usePetLog must be used within PetLogProvider");
  }
  return context;
}

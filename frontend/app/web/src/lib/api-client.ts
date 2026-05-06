import axios, { AxiosError } from "axios";
import type { ExpansionState } from "./expansion-state";
import type {
  AppSettings,
  CareSchedule,
  ChatbotMessage,
  ChatbotThread,
  PetProfile,
  RecordCategory,
  RecordEntry,
  ScheduleCategory,
  StructuredRecord,
} from "./types";

export type ApiSuccess<T> = {
  ok: true;
  data: T;
};

export type ApiFailure = {
  ok: false;
  error: {
    code: string;
    message: string;
  };
};

export type ApiResponse<T> = ApiSuccess<T> | ApiFailure;

export type PetLogSnapshot = {
  version: 1;
  profile: PetProfile;
  records: RecordEntry[];
  schedules: CareSchedule[];
  settings: AppSettings;
  readNotificationIds: string[];
  expansionState: ExpansionState;
};

export type NewRecordInput = {
  category: RecordCategory;
  detail: string;
};

export type UpdateRecordInput = {
  category: RecordCategory;
  detail: string;
};

export type StructureRecordInput = {
  detail: string;
  fallbackCategory: RecordCategory;
};

export type NewScheduleInput = {
  category: ScheduleCategory;
  title: string;
  dueDate: string;
  repeatLabel: string;
  note: string;
};

export type UpdateScheduleInput = Partial<{
  category: ScheduleCategory;
  title: string;
  dueDate: string;
  repeatLabel: string;
  note: string;
  isDone: boolean;
}>;

export type ChatbotMessageResponse = {
  answer: string;
  referencedRecordIds: string[];
  safetyNotice: string;
  threadId?: string;
  thread?: ChatbotThread;
  userMessage?: ChatbotMessage;
  assistantMessage?: ChatbotMessage;
};

export type ChatbotThreadMessageResponse = {
  thread: ChatbotThread;
  userMessage: ChatbotMessage;
  assistantMessage: ChatbotMessage;
  answer: string;
  referencedRecordIds: string[];
  safetyNotice: string;
};

export class PetLogApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "PetLogApiError";
    this.code = code;
  }
}

export const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

async function requestData<T>(request: Promise<{ data: ApiResponse<T> }>) {
  try {
    const response = await request;
    if (!response.data.ok) {
      throw new PetLogApiError(response.data.error.code, response.data.error.message);
    }
    return response.data.data;
  } catch (error) {
    if (error instanceof PetLogApiError) {
      throw error;
    }

    if (error instanceof AxiosError) {
      const data = error.response?.data as ApiFailure | undefined;
      if (data && data.ok === false) {
        throw new PetLogApiError(data.error.code, data.error.message);
      }
      throw new PetLogApiError("INTERNAL_ERROR", "API 요청을 처리하지 못했습니다.");
    }

    throw new PetLogApiError("INTERNAL_ERROR", "알 수 없는 API 오류가 발생했습니다.");
  }
}

export function getPetLogSnapshot() {
  return requestData<PetLogSnapshot>(apiClient.get("/me/pet-log"));
}

export function resetPetLogSnapshot() {
  return requestData<PetLogSnapshot>(apiClient.post("/me/pet-log/reset"));
}

export function updateProfile(input: PetProfile) {
  return requestData<{ profile: PetProfile }>(apiClient.put("/profile", input));
}

export function createRecord(input: NewRecordInput) {
  return requestData<{ record: RecordEntry }>(apiClient.post("/records", input));
}

export function structureRecordPreview(input: StructureRecordInput) {
  return requestData<{ structured: StructuredRecord }>(apiClient.post("/ai/records/structure", input));
}

export function updateRecord(id: string, input: UpdateRecordInput) {
  return requestData<{ record: RecordEntry }>(apiClient.patch(`/records/${id}`, input));
}

export function deleteRecord(id: string) {
  return requestData<{ deletedId: string }>(apiClient.delete(`/records/${id}`));
}

export function createSchedule(input: NewScheduleInput) {
  return requestData<{ schedule: CareSchedule }>(apiClient.post("/schedules", input));
}

export function updateSchedule(id: string, input: UpdateScheduleInput) {
  return requestData<{ schedule: CareSchedule }>(apiClient.patch(`/schedules/${id}`, input));
}

export function deleteSchedule(id: string) {
  return requestData<{ deletedId: string }>(apiClient.delete(`/schedules/${id}`));
}

export function updateSettings(input: AppSettings) {
  return requestData<{ settings: AppSettings }>(apiClient.put("/settings", input));
}

export function updateReadNotifications(readNotificationIds: string[]) {
  return requestData<{ readNotificationIds: string[] }>(apiClient.put("/notifications/read", { readNotificationIds }));
}

export function updateExpansionState(input: Partial<ExpansionState>) {
  return requestData<{ expansionState: ExpansionState }>(apiClient.put("/expansion-state", input));
}

export function getChatbotThreads() {
  return requestData<{ threads: ChatbotThread[] }>(apiClient.get("/chatbot/threads"));
}

export function createChatbotThread(title?: string) {
  return requestData<{ thread: ChatbotThread }>(apiClient.post("/chatbot/threads", { title }));
}

export function sendChatbotThreadMessage(threadId: string, question: string, contextRecordIds?: string[]) {
  return requestData<ChatbotThreadMessageResponse>(apiClient.post(`/chatbot/threads/${threadId}/messages`, { question, contextRecordIds }));
}

export function sendChatbotMessage(question: string, contextRecordIds?: string[], threadId?: string) {
  return requestData<ChatbotMessageResponse>(apiClient.post("/chatbot/messages", { question, contextRecordIds, threadId }));
}

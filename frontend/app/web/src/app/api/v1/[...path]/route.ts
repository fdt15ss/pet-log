import { NextRequest, NextResponse } from "next/server";
import axios from "axios";
import {
  appendMockChatbotExchange,
  createMockChatbotThread,
  getMockChatbotThreads,
  getMockPetLogSnapshot,
  updateMockExpansionState,
  updateMockSettings,
} from "@/lib/server/mock-pet-log-store";
import { createPetLogChatbotMessage } from "@/lib/server/pet-log-ai-service";
import {
  ExtractedMeasurement,
  RecordCategory,
  RecordCategoryChoice,
  RecordEntry,
  RecordStatus,
  StructuredRecord,
} from "@/lib/types";

type RouteContext = {
  params: Promise<{
    path?: string[];
  }>;
};

const recordCategories: RecordCategory[] = ["meal", "walk", "stool", "medical", "behavior"];
const recordStatuses: RecordStatus[] = ["normal", "notice", "alert"];
const defaultBackendApiBaseUrl = "http://127.0.0.1:27893";
const defaultBackendPetId = "pet_01JCM7V8H9Q2K4N6R8T0A1B2C3";
const defaultBackendTimeoutMs = 60000;

type BackendPetLogCandidate = {
  title?: unknown;
  detail?: unknown;
  category?: unknown;
  status?: unknown;
  confidence?: unknown;
  needs_confirmation?: unknown;
  measurements?: unknown;
};

type BackendPetLogRecord = {
  id?: unknown;
  category?: unknown;
  title?: unknown;
  detail?: unknown;
  status?: unknown;
  recorded_at?: unknown;
};

type BackendRecordEntry = {
  id?: unknown;
  date?: unknown;
  time?: unknown;
  category?: unknown;
  title?: unknown;
  detail?: unknown;
  status?: unknown;
};

type BackendPetLogResult = {
  candidates?: unknown;
  saved_records?: unknown;
  needs_confirmation?: unknown;
};

class BackendRouteError extends Error {
  status: number;
  code: string;

  constructor(code: string, message: string, status = 502) {
    super(message);
    this.name = "BackendRouteError";
    this.code = code;
    this.status = status;
  }
}

function ok<T>(data: T, status = 200) {
  return NextResponse.json({ ok: true, data }, { status });
}

function fail(code: string, message: string, status = 400) {
  return NextResponse.json({ ok: false, error: { code, message } }, { status });
}

function isRecordCategory(value: unknown): value is RecordCategory {
  return recordCategories.includes(value as RecordCategory);
}

function isRecordCategoryChoice(value: unknown): value is RecordCategoryChoice {
  return value === "all" || isRecordCategory(value);
}

function isRecordStatus(value: unknown): value is RecordStatus {
  return recordStatuses.includes(value as RecordStatus);
}

async function readJson(request: NextRequest) {
  try {
    return await request.json();
  } catch {
    return null;
  }
}

async function getPath(context: RouteContext) {
  const params = await context.params;
  return params.path ?? [];
}

function isSpeechTranscriptionPath(path: string[]) {
  return path[0] === "speech" && path[1] === "transcriptions" && path.length === 2;
}

function backendApiUrl(path: string) {
  const baseUrl = process.env.PET_LOG_BACKEND_API_BASE_URL ?? defaultBackendApiBaseUrl;
  return `${baseUrl.replace(/\/$/, "")}${path}`;
}

function backendPetId() {
  return process.env.PET_LOG_BACKEND_PET_ID ?? defaultBackendPetId;
}

function backendTimeoutMs() {
  const configured = Number(process.env.PET_LOG_BACKEND_TIMEOUT_MS);
  return Number.isFinite(configured) && configured > 0 ? configured : defaultBackendTimeoutMs;
}

function formatBackendDateLabel(recordedAt: string) {
  const date = new Date(recordedAt);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return `${date.getMonth() + 1}월 ${date.getDate()}일`;
}

function formatBackendTimeLabel(recordedAt: string) {
  const date = new Date(recordedAt);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function mapBackendMeasurements(measurements: unknown): ExtractedMeasurement[] {
  if (!Array.isArray(measurements)) {
    return [];
  }

  return measurements
    .map((measurement) => {
      if (typeof measurement === "string" && measurement.trim()) {
        return { label: "측정값", value: measurement.trim() };
      }

      if (
        measurement &&
        typeof measurement === "object" &&
        typeof (measurement as ExtractedMeasurement).label === "string" &&
        typeof (measurement as ExtractedMeasurement).value === "string"
      ) {
        return {
          label: (measurement as ExtractedMeasurement).label.trim() || "측정값",
          value: (measurement as ExtractedMeasurement).value.trim(),
        };
      }

      return null;
    })
    .filter((measurement): measurement is ExtractedMeasurement => !!measurement && !!measurement.value)
    .slice(0, 4);
}

function firstBackendCandidate(result: BackendPetLogResult): BackendPetLogCandidate | null {
  if (!Array.isArray(result.candidates)) {
    return null;
  }

  const candidate = result.candidates[0];
  return candidate && typeof candidate === "object" ? (candidate as BackendPetLogCandidate) : null;
}

function backendCandidateCategories(result: BackendPetLogResult): RecordCategory[] {
  if (!Array.isArray(result.candidates)) {
    return [];
  }

  return result.candidates.reduce<RecordCategory[]>((categories, candidate) => {
    const category =
      candidate && typeof candidate === "object" ? (candidate as BackendPetLogCandidate).category : null;
    if (!isRecordCategory(category) || categories.includes(category)) {
      return categories;
    }
    return [...categories, category];
  }, []);
}

function firstBackendSavedRecord(result: BackendPetLogResult): BackendPetLogRecord | null {
  if (!Array.isArray(result.saved_records)) {
    return null;
  }

  const record = result.saved_records[0];
  return record && typeof record === "object" ? (record as BackendPetLogRecord) : null;
}

function mapBackendCandidateToStructured(
  candidate: BackendPetLogCandidate,
  detail: string,
  fallbackCategory: RecordCategoryChoice,
  resultNeedsConfirmation: unknown,
  detectedCategories: RecordCategory[] = [],
): StructuredRecord {
  const category = isRecordCategory(candidate.category) ? candidate.category : fallbackCategory === "all" ? "meal" : fallbackCategory;
  const confidence =
    typeof candidate.confidence === "number" ? Math.min(0.99, Math.max(0.1, candidate.confidence)) : 0.45;
  const candidateTitle = typeof candidate.title === "string" && candidate.title.trim() ? candidate.title.trim() : "";
  const candidateDetail = typeof candidate.detail === "string" && candidate.detail.trim() ? candidate.detail.trim() : detail;

  return {
    sourceText: candidateDetail,
    normalizedSummary: candidateTitle || candidateDetail.slice(0, 80),
    suggestedCategory: category,
    detectedCategories: detectedCategories.length > 1 ? detectedCategories : undefined,
    confidence,
    measurements: mapBackendMeasurements(candidate.measurements),
    needsConfirmation:
      typeof candidate.needs_confirmation === "boolean"
        ? candidate.needs_confirmation
        : typeof resultNeedsConfirmation === "boolean"
          ? resultNeedsConfirmation
          : confidence < 0.7 || (fallbackCategory !== "all" && category !== fallbackCategory),
  };
}

function mapBackendRecordToEntry(
  record: BackendPetLogRecord,
  structured: StructuredRecord,
  fallbackCategory: RecordCategory,
  categoryChoice?: RecordCategoryChoice,
): RecordEntry | null {
  if (
    typeof record.id !== "string" ||
    typeof record.title !== "string" ||
    typeof record.detail !== "string" ||
    typeof record.recorded_at !== "string"
  ) {
    return null;
  }

  const date = formatBackendDateLabel(record.recorded_at);
  const time = formatBackendTimeLabel(record.recorded_at);
  if (!date || !time) {
    return null;
  }

  return {
    id: record.id,
    date,
    time,
    category: isRecordCategory(record.category) ? record.category : fallbackCategory,
    categoryChoice,
    title: record.title,
    detail: record.detail,
    status: isRecordStatus(record.status) ? record.status : "normal",
    structured,
  };
}

async function requestBackendPetLogRecord(detail: string, fallbackCategory: RecordCategoryChoice, confirm: boolean) {
  const response = await axios.post<{ success?: boolean; data?: BackendPetLogResult; detail?: unknown }>(
    backendApiUrl("/api/v1/pet-log/records"),
    {
      pet_id: backendPetId(),
      text: detail,
      source: confirm ? "manual" : "ai_preview",
      confirm,
    },
    {
      headers: {
        "Content-Type": "application/json",
      },
      timeout: backendTimeoutMs(),
      validateStatus: () => true,
    },
  );

  const payload = response.data;
  if (response.status < 200 || response.status >= 300 || payload?.success !== true || !payload.data) {
    const message = typeof payload?.detail === "string" ? payload.detail : "기록 서버 요청을 처리하지 못했습니다.";
    throw new BackendRouteError("BACKEND_RECORD_FAILED", message, response.status || 502);
  }

  const candidate = firstBackendCandidate(payload.data);
  if (!candidate) {
    throw new BackendRouteError("BACKEND_RECORD_FAILED", "기록 서버 응답에 구조화 후보가 없습니다.");
  }

  const structured = mapBackendCandidateToStructured(
    candidate,
    detail,
    fallbackCategory,
    payload.data.needs_confirmation,
    backendCandidateCategories(payload.data),
  );
  return { result: payload.data, structured };
}

async function proxySpeechTranscription(request: NextRequest) {
  const incomingFormData = await request.formData();
  const audio = incomingFormData.get("audio");
  if (!(audio instanceof File)) {
    return fail("VALIDATION_ERROR", "음성 파일이 필요합니다.", 400);
  }

  const backendFormData = new FormData();
  backendFormData.set("audio", audio);

  const response = await fetch(backendApiUrl("/api/v1/speech/transcriptions"), {
    body: backendFormData,
    method: "POST",
  });

  const payload = (await response.json().catch(() => null)) as
    | { success?: boolean; data?: { text?: unknown }; detail?: unknown }
    | null;

  if (!response.ok || payload?.success !== true || typeof payload.data?.text !== "string") {
    const message = typeof payload?.detail === "string" ? payload.detail : "음성 인식을 처리하지 못했습니다.";
    return fail("SPEECH_TRANSCRIPTION_FAILED", message, response.status || 502);
  }

  return ok({ text: payload.data.text });
}

async function proxyFileUpload(request: NextRequest) {
  const incomingFormData = await request.formData();
  const file = incomingFormData.get("file");
  if (!(file instanceof File)) {
    return fail("VALIDATION_ERROR", "이미지 파일이 필요합니다.", 400);
  }

  const backendFormData = new FormData();
  backendFormData.set("file", file);
  backendFormData.set("pet_id", backendPetId());
  backendFormData.set("purpose", "profile_photo");

  const response = await fetch(backendApiUrl("/api/v1/files"), {
    body: backendFormData,
    method: "POST",
  });
  const payload = (await response.json().catch(() => null)) as
    | { success?: boolean; data?: unknown; detail?: unknown }
    | null;

  if (!response.ok || payload?.success !== true || !payload.data) {
    const message = typeof payload?.detail === "string" ? payload.detail : "이미지를 저장하지 못했습니다.";
    return fail("FILE_UPLOAD_FAILED", message, response.status || 502);
  }

  return ok(payload.data, response.status);
}

async function proxyFileDownload(fileId: string) {
  const response = await fetch(backendApiUrl(`/api/v1/files/${encodeURIComponent(fileId)}`));
  if (!response.ok) {
    return fail("FILE_NOT_FOUND", "이미지를 찾지 못했습니다.", response.status || 404);
  }

  const headers = new Headers();
  const contentType = response.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  headers.set("cache-control", "public, max-age=31536000, immutable");
  return new NextResponse(await response.arrayBuffer(), { status: response.status, headers });
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const path = await getPath(context);

  if (path[0] === "files" && path[1] && path.length === 2) {
    return proxyFileDownload(path[1]);
  }

  if (path[0] === "me" && path.length === 1) {
    try {
      const response = await axios.get(backendApiUrl("/api/v1/me"), { timeout: backendTimeoutMs(), validateStatus: () => true });
      return ok(response.data.data);
    } catch {
      return fail("BACKEND_ME_FAILED", "내 정보를 불러오지 못했습니다.", 502);
    }
  }

  if (path[0] === "pets" && path.length === 1) {
    try {
      const response = await axios.get(backendApiUrl("/api/v1/pets"), { timeout: backendTimeoutMs(), validateStatus: () => true });
      const data = response.data?.data;
      if (data && Array.isArray(data.pets)) {
        return ok(data);
      }
      return fail("BACKEND_PETS_FAILED", "반려동물 목록 응답 형식이 올바르지 않습니다.", 502);
    } catch {
      return fail("BACKEND_PETS_FAILED", "반려동물 목록을 불러오지 못했습니다.", 502);
    }
  }

  if (path[0] === "notifications" && path.length === 1) {
    const petId = _request.nextUrl.searchParams.get("pet_id") || backendPetId();
    try {
      const response = await axios.get(backendApiUrl(`/api/v1/notifications?pet_id=${encodeURIComponent(petId)}`), {
        timeout: backendTimeoutMs(),
        validateStatus: () => true,
      });
      return ok(response.data.data);
    } catch {
      return fail("BACKEND_NOTIFICATION_FAILED", "알림 목록을 불러오지 못했습니다.", 502);
    }
  }

  if (path[0] === "pet-log" && path[1] === "records" && path.length === 2) {
    const petId = _request.nextUrl.searchParams.get("pet_id") || backendPetId();
    try {
      const response = await axios.get(backendApiUrl(`/api/v1/pet-log/records?pet_id=${encodeURIComponent(petId)}`), {
        timeout: backendTimeoutMs(),
        validateStatus: () => true,
      });
      return ok(response.data.data);
    } catch {
      return fail("BACKEND_RECORDS_FAILED", "기록 목록을 불러오지 못했습니다.", 502);
    }
  }

  if (path[0] === "pet-log" && path[1] === "schedules" && path.length === 2) {
    const petId = _request.nextUrl.searchParams.get("pet_id") || backendPetId();
    try {
      const response = await axios.get(backendApiUrl(`/api/v1/pet-log/schedules?pet_id=${encodeURIComponent(petId)}`), {
        timeout: backendTimeoutMs(),
        validateStatus: () => true,
      });
      return ok(response.data.data);
    } catch {
      return fail("BACKEND_SCHEDULES_FAILED", "일정 목록을 불러오지 못했습니다.", 502);
    }
  }

  if (path[0] === "ai" && path[1] === "insights" && path.length === 2) {
    const petId = _request.nextUrl.searchParams.get("pet_id") || backendPetId();
    try {
      const response = await axios.get(backendApiUrl(`/api/v1/ai/insights?pet_id=${encodeURIComponent(petId)}`), {
        timeout: backendTimeoutMs(),
        validateStatus: () => true,
      });
      return ok(response.data.data);
    } catch {
      return fail("BACKEND_INSIGHTS_FAILED", "AI 분석 결과를 불러오지 못했습니다.", 502);
    }
  }

  if (path[0] === "ai" && path[1] === "suggestions" && path.length === 2) {
    const petId = _request.nextUrl.searchParams.get("pet_id") || backendPetId();
    try {
      const response = await axios.get(backendApiUrl(`/api/v1/ai/suggestions?pet_id=${encodeURIComponent(petId)}`), {
        timeout: backendTimeoutMs(),
        validateStatus: () => true,
      });
      return ok(response.data.data);
    } catch {
      return fail("BACKEND_SUGGESTIONS_FAILED", "AI 케어 제안을 불러오지 못했습니다.", 502);
    }
  }

  if (path[0] === "chatbot" && path[1] === "threads" && path.length === 2) {
    return ok({ threads: getMockChatbotThreads() });
  }

  return fail("NOT_FOUND", "요청한 API를 찾을 수 없습니다.", 404);
}

export async function POST(request: NextRequest, context: RouteContext) {
  const path = await getPath(context);
  if (isSpeechTranscriptionPath(path)) {
    return proxySpeechTranscription(request);
  }
  if (path[0] === "files" && path.length === 1) {
    return proxyFileUpload(request);
  }

  const body = await readJson(request);

  if (path[0] === "records" && path.length === 1) {
    if (!body || typeof body.detail !== "string" || !isRecordCategoryChoice(body.category)) {
      return fail("VALIDATION_ERROR", "기록 카테고리와 내용을 입력해주세요.");
    }
    try {
      const { result, structured } = await requestBackendPetLogRecord(body.detail, body.category, true);
      const savedRecord = firstBackendSavedRecord(result);
      const record = savedRecord
        ? mapBackendRecordToEntry(savedRecord, structured, structured.suggestedCategory, body.category)
        : null;
      if (record) {
        return ok({ record }, 201);
      }
      return fail("BACKEND_RECORD_FAILED", "기록 서버 응답에 저장된 기록이 없습니다.", 502);
    } catch {
      return fail("BACKEND_RECORD_FAILED", "기록 서버 요청을 처리하지 못했습니다.", 502);
    }
  }

  if (path[0] === "ai" && path[1] === "records" && path[2] === "structure" && path.length === 3) {
    if (!body || typeof body.detail !== "string" || !isRecordCategoryChoice(body.fallbackCategory)) {
      return fail("VALIDATION_ERROR", "구조화할 기록 내용과 기본 카테고리를 입력해주세요.");
    }
    try {
      const { structured } = await requestBackendPetLogRecord(body.detail, body.fallbackCategory, false);
      return ok({ structured });
    } catch (error) {
      console.error("[api/ai/records/structure] Error:", error);
      const status = error instanceof BackendRouteError ? error.status : 502;
      const code = error instanceof BackendRouteError ? error.code : "BACKEND_RECORD_FAILED";
      const message = error instanceof Error ? error.message : "기록 서버 요청을 처리하지 못했습니다.";
      return fail(code, message, status);
    }
  }

  if (path[0] === "schedules" && path.length === 1) {
    if (!body || typeof body.title !== "string" || typeof body.dueDate !== "string" || typeof body.category !== "string") {
      return fail("VALIDATION_ERROR", "일정 분류, 제목, 예정일을 입력해주세요.");
    }
    try {
      const response = await axios.post<{ success?: boolean; data?: unknown; detail?: unknown }>(
        backendApiUrl("/api/v1/pet-log/schedules"),
        {
          pet_id: backendPetId(),
          category: body.category,
          title: body.title,
          dueDate: body.dueDate,
          repeatLabel: typeof body.repeatLabel === "string" ? body.repeatLabel : "한 번",
          note: typeof body.note === "string" ? body.note : "",
        },
        { headers: { "Content-Type": "application/json" }, timeout: backendTimeoutMs(), validateStatus: () => true },
      );
      if (response.status < 200 || response.status >= 300 || response.data?.success !== true || !response.data.data) {
        return fail("BACKEND_SCHEDULE_FAILED", "일정 생성을 처리하지 못했습니다.", 502);
      }
      return ok({ schedule: response.data.data }, 201);
    } catch {
      return fail("BACKEND_SCHEDULE_FAILED", "일정 생성을 처리하지 못했습니다.", 502);
    }
  }

  if (path[0] === "chatbot" && path[1] === "threads" && path.length === 2) {
    const title = body && typeof body.title === "string" && body.title.trim() ? body.title : "새 질문";
    return ok({ thread: createMockChatbotThread(title) }, 201);
  }

  if (path[0] === "chatbot" && path[1] === "threads" && path[2] && path[3] === "messages" && path.length === 4) {
    if (!body || typeof body.question !== "string" || !body.question.trim()) {
      return fail("VALIDATION_ERROR", "질문을 입력해주세요.");
    }
    const message = await createPetLogChatbotMessage({
      question: body.question,
      contextRecordIds: Array.isArray(body.contextRecordIds) ? body.contextRecordIds : [],
      snapshot: getMockPetLogSnapshot(),
    });
    const exchange = appendMockChatbotExchange(path[2], body.question, message);
    if (!exchange) {
      return fail("NOT_FOUND", "대화방을 찾을 수 없습니다.", 404);
    }
    return ok({
      ...exchange,
      answer: message.answer,
      referencedRecordIds: message.referencedRecordIds,
      safetyNotice: message.safetyNotice,
    });
  }

  if (path[0] === "chatbot" && path[1] === "messages" && path.length === 2) {
    if (!body || typeof body.question !== "string" || !body.question.trim()) {
      return fail("VALIDATION_ERROR", "질문을 입력해주세요.");
    }
    const message = await createPetLogChatbotMessage({
      question: body.question,
      contextRecordIds: Array.isArray(body.contextRecordIds) ? body.contextRecordIds : [],
      snapshot: getMockPetLogSnapshot(),
    });
    const exchange = appendMockChatbotExchange(typeof body.threadId === "string" ? body.threadId : undefined, body.question, message);
    if (!exchange) {
      return fail("NOT_FOUND", "대화방을 찾을 수 없습니다.", 404);
    }
    return ok({
      ...message,
      threadId: exchange.thread.id,
      thread: exchange.thread,
      userMessage: exchange.userMessage,
      assistantMessage: exchange.assistantMessage,
    });
  }

  if (path[0] === "pets" && path.length === 1) {
    if (!body || typeof body.name !== "string") {
      return fail("VALIDATION_ERROR", "이름은 필수입니다.");
    }
    try {
      const response = await axios.post(backendApiUrl("/api/v1/pets"), body, { timeout: backendTimeoutMs(), validateStatus: () => true });
      return ok(response.data.data, 201);
    } catch {
      return fail("BACKEND_PET_CREATE_FAILED", "반려동물을 추가하지 못했습니다.", 502);
    }
  }

  return fail("NOT_FOUND", "요청한 API를 찾을 수 없습니다.", 404);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  const path = await getPath(context);
  const body = await readJson(request);

  if (path[0] === "profile" && path.length === 1) {
    if (!body || typeof body.name !== "string" || typeof body.breed !== "string") {
      return fail("VALIDATION_ERROR", "이름과 품종은 필수입니다.");
    }
    try {
      const response = await axios.put<{ success?: boolean; data?: unknown; detail?: unknown }>(
        backendApiUrl("/api/v1/pet-log/profile"),
        {
          pet_id: backendPetId(),
          ...body,
        },
        { headers: { "Content-Type": "application/json" }, timeout: backendTimeoutMs(), validateStatus: () => true },
      );
      if (response.status < 200 || response.status >= 300 || response.data?.success !== true || !response.data.data) {
        return fail("BACKEND_PROFILE_FAILED", "프로필 수정을 처리하지 못했습니다.", 502);
      }
      return ok({ profile: response.data.data });
    } catch {
      return fail("BACKEND_PROFILE_FAILED", "프로필 수정을 처리하지 못했습니다.", 502);
    }
  }

  if (path[0] === "settings" && path.length === 1) {
    if (!body || typeof body.aiInsightEnabled !== "boolean" || !body.notificationPreferences) {
      return fail("VALIDATION_ERROR", "설정 형식이 올바르지 않습니다.");
    }
    return ok({ settings: updateMockSettings(body) });
  }

  if (path[0] === "notifications" && path[1] === "read" && path.length === 2) {
    if (!body || !Array.isArray(body.readNotificationIds)) {
      return fail("VALIDATION_ERROR", "읽음 처리할 알림 ID가 필요합니다.");
    }
    try {
      // 현재 백엔드는 pet_id 기준 일괄 읽음만 지원하므로 루프 돌리거나 일괄 API 호출
      const response = await axios.put<{ success?: boolean; data?: unknown; detail?: unknown }>(
        backendApiUrl(`/api/v1/notifications/read?pet_id=${encodeURIComponent(backendPetId())}`),
        {},
        { timeout: backendTimeoutMs(), validateStatus: () => true },
      );
      if (response.status < 200 || response.status >= 300 || response.data?.success !== true) {
        return fail("BACKEND_NOTIFICATION_FAILED", "알림 읽음 처리를 실패했습니다.", 502);
      }
      return ok({ readNotificationIds: body.readNotificationIds });
    } catch {
      return fail("BACKEND_NOTIFICATION_FAILED", "알림 읽음 처리를 실패했습니다.", 502);
    }
  }

  if (path[0] === "expansion-state" && path.length === 1) {
    if (!body || typeof body !== "object") {
      return fail("VALIDATION_ERROR", "확장 상태 형식이 올바르지 않습니다.");
    }
    return ok({ expansionState: updateMockExpansionState(body) });
  }

  return fail("NOT_FOUND", "요청한 API를 찾을 수 없습니다.", 404);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  const path = await getPath(context);
  const body = await readJson(request);

  if (path[0] === "records" && path[1] && path.length === 2) {
    if (!body || typeof body.detail !== "string" || !isRecordCategoryChoice(body.category)) {
      return fail("VALIDATION_ERROR", "기록 카테고리와 내용을 입력해주세요.");
    }
    try {
      const { result, structured } = await requestBackendPetLogRecord(body.detail, body.category, false);
      const candidate = firstBackendCandidate(result);
      const category: RecordCategory = isRecordCategory(candidate?.category)
        ? (candidate!.category as RecordCategory)
        : body.category === "all" ? "meal" : (body.category as RecordCategory);
      const title = typeof candidate?.title === "string" && candidate.title.trim()
        ? candidate.title.trim()
        : (body.detail as string).slice(0, 80);
      const status: RecordStatus = isRecordStatus(candidate?.status) ? (candidate!.status as RecordStatus) : "normal";

      const patchResp = await axios.patch<{ success?: boolean; data?: unknown; detail?: unknown }>(
        backendApiUrl(`/api/v1/pet-log/records/${encodeURIComponent(path[1])}`),
        { detail: body.detail, category, title, status },
        { headers: { "Content-Type": "application/json" }, timeout: backendTimeoutMs(), validateStatus: () => true },
      );
      if (patchResp.status === 404) {
        return fail("NOT_FOUND", "수정할 기록을 찾을 수 없습니다.", 404);
      }
      if (patchResp.status < 200 || patchResp.status >= 300 || patchResp.data?.success !== true) {
        return fail("BACKEND_RECORD_FAILED", "기록 수정을 처리하지 못했습니다.", 502);
      }
      const updated = patchResp.data.data as BackendRecordEntry | null;
      if (!updated || typeof updated.id !== "string") {
        return fail("BACKEND_RECORD_FAILED", "기록 수정 응답 형식이 올바르지 않습니다.", 502);
      }
      const record: RecordEntry = {
        id: updated.id,
        date: typeof updated.date === "string" ? updated.date : "",
        time: typeof updated.time === "string" ? updated.time : "",
        category,
        categoryChoice: body.category,
        title,
        detail: body.detail,
        status,
        structured,
      };
      return ok({ record });
    } catch {
      return fail("BACKEND_RECORD_FAILED", "기록 수정을 처리하지 못했습니다.", 502);
    }
  }

  if (path[0] === "schedules" && path[1] && path.length === 2) {
    if (!body || typeof body !== "object") {
      return fail("VALIDATION_ERROR", "일정 수정 내용이 필요합니다.");
    }
    try {
      const patchResp = await axios.patch<{ success?: boolean; data?: unknown; detail?: unknown }>(
        backendApiUrl(`/api/v1/pet-log/schedules/${encodeURIComponent(path[1])}`),
        body,
        { headers: { "Content-Type": "application/json" }, timeout: backendTimeoutMs(), validateStatus: () => true },
      );
      if (patchResp.status === 404) {
        return fail("NOT_FOUND", "수정할 일정을 찾을 수 없습니다.", 404);
      }
      if (patchResp.status < 200 || patchResp.status >= 300 || patchResp.data?.success !== true || !patchResp.data.data) {
        return fail("BACKEND_SCHEDULE_FAILED", "일정 수정을 처리하지 못했습니다.", 502);
      }
      return ok({ schedule: patchResp.data.data });
    } catch {
      return fail("BACKEND_SCHEDULE_FAILED", "일정 수정을 처리하지 못했습니다.", 502);
    }
  }

  if (path[0] === "pets" && path[1] && path.length === 2) {
    try {
      const response = await axios.patch(backendApiUrl(`/api/v1/pets/${encodeURIComponent(path[1])}`), body, { timeout: backendTimeoutMs(), validateStatus: () => true });
      if (response.status === 404) return fail("NOT_FOUND", "반려동물을 찾을 수 없습니다.", 404);
      return ok(response.data.data);
    } catch {
      return fail("BACKEND_PET_UPDATE_FAILED", "반려동물 정보를 수정하지 못했습니다.", 502);
    }
  }

  if (path[0] === "notifications" && path[1] && path[2] === "read" && path.length === 3) {
    try {
      const response = await axios.patch(backendApiUrl(`/api/v1/notifications/${encodeURIComponent(path[1])}/read`), {}, { timeout: backendTimeoutMs(), validateStatus: () => true });
      if (response.status === 404) return fail("NOT_FOUND", "알림을 찾을 수 없습니다.", 404);
      return ok(response.data.data);
    } catch {
      return fail("BACKEND_NOTIFICATION_FAILED", "알림 읽음 처리를 실패했습니다.", 502);
    }
  }

  return fail("NOT_FOUND", "요청한 API를 찾을 수 없습니다.", 404);
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const path = await getPath(context);

  if (path[0] === "records" && path[1] && path.length === 2) {
    try {
      const response = await axios.delete<{ success?: boolean; data?: unknown; detail?: unknown }>(
        backendApiUrl(`/api/v1/pet-log/records/${encodeURIComponent(path[1])}`),
        { timeout: backendTimeoutMs(), validateStatus: () => true },
      );
      if (response.status === 404) {
        return fail("NOT_FOUND", "삭제할 기록을 찾을 수 없습니다.", 404);
      }
      if (response.status < 200 || response.status >= 300 || response.data?.success !== true) {
        return fail("BACKEND_RECORD_FAILED", "기록 삭제를 처리하지 못했습니다.", 502);
      }
      return ok({ deletedId: path[1] });
    } catch {
      return fail("BACKEND_RECORD_FAILED", "기록 삭제를 처리하지 못했습니다.", 502);
    }
  }

  if (path[0] === "schedules" && path[1] && path.length === 2) {
    try {
      const response = await axios.delete<{ success?: boolean; data?: unknown; detail?: unknown }>(
        backendApiUrl(`/api/v1/pet-log/schedules/${encodeURIComponent(path[1])}`),
        { timeout: backendTimeoutMs(), validateStatus: () => true },
      );
      if (response.status === 404) {
        return fail("NOT_FOUND", "삭제할 일정을 찾을 수 없습니다.", 404);
      }
      if (response.status < 200 || response.status >= 300 || response.data?.success !== true) {
        return fail("BACKEND_SCHEDULE_FAILED", "일정 삭제를 처리하지 못했습니다.", 502);
      }
      return ok({ deletedId: path[1] });
    } catch {
      return fail("BACKEND_SCHEDULE_FAILED", "일정 삭제를 처리하지 못했습니다.", 502);
    }
  }

  if (path[0] === "pets" && path[1] && path.length === 2) {
    try {
      const response = await axios.delete(backendApiUrl(`/api/v1/pets/${encodeURIComponent(path[1])}`), { timeout: backendTimeoutMs(), validateStatus: () => true });
      if (response.status === 404) return fail("NOT_FOUND", "삭제할 반려동물을 찾을 수 없습니다.", 404);
      return ok({ deletedId: path[1] });
    } catch {
      return fail("BACKEND_PET_DELETE_FAILED", "반려동물을 삭제하지 못했습니다.", 502);
    }
  }

  return fail("NOT_FOUND", "요청한 API를 찾을 수 없습니다.", 404);
}

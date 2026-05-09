import { NextRequest, NextResponse } from "next/server";
import axios from "axios";
import {
  appendMockChatbotExchange,
  createMockChatbotThread,
  createMockRecord,
  createMockSchedule,
  deleteMockRecord,
  deleteMockSchedule,
  getMockChatbotThreads,
  getMockPetLogSnapshot,
  resetMockPetLogSnapshot,
  updateMockExpansionState,
  updateMockProfile,
  updateMockReadNotifications,
  updateMockRecord,
  updateMockSchedule,
  updateMockSettings,
} from "@/lib/server/mock-pet-log-store";
import { createPetLogChatbotMessage, createPetLogStructuredRecord } from "@/lib/server/pet-log-ai-service";
import type { ExtractedMeasurement, RecordCategory, RecordCategoryChoice, RecordEntry, RecordStatus, StructuredRecord } from "@/lib/types";

type RouteContext = {
  params: Promise<{
    path?: string[];
  }>;
};

const recordCategories: RecordCategory[] = ["meal", "walk", "stool", "medical", "behavior"];
const recordStatuses: RecordStatus[] = ["normal", "notice", "alert"];
const defaultBackendApiBaseUrl = "http://127.0.0.1:8000";
const defaultBackendPetId = "pet_01JCM7V8H9Q2K4N6R8T0A1B2C3";
const defaultBackendTimeoutMs = 1200;

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

type BackendPetLogResult = {
  candidates?: unknown;
  saved_records?: unknown;
  needs_confirmation?: unknown;
};

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
    throw new Error(message);
  }

  const candidate = firstBackendCandidate(payload.data);
  if (!candidate) {
    throw new Error("기록 서버 응답에 구조화 후보가 없습니다.");
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

export async function GET(_request: NextRequest, context: RouteContext) {
  const path = await getPath(context);

  if (path[0] === "me" && path[1] === "pet-log" && path.length === 2) {
    return ok(getMockPetLogSnapshot());
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

  const body = await readJson(request);

  if (path[0] === "me" && path[1] === "pet-log" && path[2] === "reset" && path.length === 3) {
    return ok(resetMockPetLogSnapshot());
  }

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
    } catch {
      // 백엔드가 준비되지 않은 개발 환경에서는 기존 mock 저장 경로를 유지합니다.
    }
    const structured = await createPetLogStructuredRecord({ fallbackCategory: body.category, detail: body.detail });
    const category = body.category === "all" ? structured.suggestedCategory : body.category;
    return ok({ record: createMockRecord({ category, categoryChoice: body.category, detail: body.detail, structured }) }, 201);
  }

  if (path[0] === "ai" && path[1] === "records" && path[2] === "structure" && path.length === 3) {
    if (!body || typeof body.detail !== "string" || !isRecordCategoryChoice(body.fallbackCategory)) {
      return fail("VALIDATION_ERROR", "구조화할 기록 내용과 기본 카테고리를 입력해주세요.");
    }
    try {
      const { structured } = await requestBackendPetLogRecord(body.detail, body.fallbackCategory, false);
      return ok({ structured });
    } catch {
      // 백엔드 미연결 시 프론트 서버의 mock AI 구조화를 그대로 사용합니다.
    }
    const structured = await createPetLogStructuredRecord({ detail: body.detail, fallbackCategory: body.fallbackCategory });
    return ok({ structured });
  }

  if (path[0] === "schedules" && path.length === 1) {
    if (!body || typeof body.title !== "string" || typeof body.dueDate !== "string" || typeof body.category !== "string") {
      return fail("VALIDATION_ERROR", "일정 분류, 제목, 예정일을 입력해주세요.");
    }
    return ok(
      {
        schedule: createMockSchedule({
          category: body.category,
          title: body.title,
          dueDate: body.dueDate,
          repeatLabel: typeof body.repeatLabel === "string" ? body.repeatLabel : "한 번",
          note: typeof body.note === "string" ? body.note : "",
        }),
      },
      201,
    );
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

  return fail("NOT_FOUND", "요청한 API를 찾을 수 없습니다.", 404);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  const path = await getPath(context);
  const body = await readJson(request);

  if (path[0] === "profile" && path.length === 1) {
    if (!body || typeof body.name !== "string" || typeof body.breed !== "string") {
      return fail("VALIDATION_ERROR", "이름과 품종은 필수입니다.");
    }
    return ok({ profile: updateMockProfile(body) });
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
    return ok({ readNotificationIds: updateMockReadNotifications(body.readNotificationIds) });
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

    const structured = await createPetLogStructuredRecord({ fallbackCategory: body.category, detail: body.detail });
    const existingRecord = getMockPetLogSnapshot().records.find((record) => record.id === path[1]);
    const category =
      body.category === "all"
        ? structured.confidence < 0.7
          ? existingRecord?.category ?? structured.suggestedCategory
          : structured.suggestedCategory
        : body.category;
    const record = updateMockRecord(path[1], { category, categoryChoice: body.category, detail: body.detail, structured });
    if (!record) {
      return fail("NOT_FOUND", "수정할 기록을 찾을 수 없습니다.", 404);
    }
    return ok({ record });
  }

  if (path[0] === "schedules" && path[1] && path.length === 2) {
    if (!body || typeof body !== "object") {
      return fail("VALIDATION_ERROR", "일정 수정 내용이 필요합니다.");
    }

    const schedule = updateMockSchedule(path[1], body);
    if (!schedule) {
      return fail("NOT_FOUND", "수정할 일정을 찾을 수 없습니다.", 404);
    }
    return ok({ schedule });
  }

  return fail("NOT_FOUND", "요청한 API를 찾을 수 없습니다.", 404);
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const path = await getPath(context);

  if (path[0] === "records" && path[1] && path.length === 2) {
    if (!deleteMockRecord(path[1])) {
      return fail("NOT_FOUND", "삭제할 기록을 찾을 수 없습니다.", 404);
    }
    return ok({ deletedId: path[1] });
  }

  if (path[0] === "schedules" && path[1] && path.length === 2) {
    if (!deleteMockSchedule(path[1])) {
      return fail("NOT_FOUND", "삭제할 일정을 찾을 수 없습니다.", 404);
    }
    return ok({ deletedId: path[1] });
  }

  return fail("NOT_FOUND", "요청한 API를 찾을 수 없습니다.", 404);
}

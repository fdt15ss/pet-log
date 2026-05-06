import { NextRequest, NextResponse } from "next/server";
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
import type { RecordCategory } from "@/lib/types";

type RouteContext = {
  params: Promise<{
    path?: string[];
  }>;
};

const recordCategories: RecordCategory[] = ["meal", "walk", "stool", "medical", "behavior"];

function ok<T>(data: T, status = 200) {
  return NextResponse.json({ ok: true, data }, { status });
}

function fail(code: string, message: string, status = 400) {
  return NextResponse.json({ ok: false, error: { code, message } }, { status });
}

function isRecordCategory(value: unknown): value is RecordCategory {
  return recordCategories.includes(value as RecordCategory);
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
  const body = await readJson(request);

  if (path[0] === "me" && path[1] === "pet-log" && path[2] === "reset" && path.length === 3) {
    return ok(resetMockPetLogSnapshot());
  }

  if (path[0] === "records" && path.length === 1) {
    if (!body || typeof body.detail !== "string" || !isRecordCategory(body.category)) {
      return fail("VALIDATION_ERROR", "기록 카테고리와 내용을 입력해주세요.");
    }
    const structured = await createPetLogStructuredRecord({ fallbackCategory: body.category, detail: body.detail });
    return ok({ record: createMockRecord({ category: body.category, detail: body.detail, structured }) }, 201);
  }

  if (path[0] === "ai" && path[1] === "records" && path[2] === "structure" && path.length === 3) {
    if (!body || typeof body.detail !== "string" || !isRecordCategory(body.fallbackCategory)) {
      return fail("VALIDATION_ERROR", "구조화할 기록 내용과 기본 카테고리를 입력해주세요.");
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
    if (!body || typeof body.detail !== "string" || !isRecordCategory(body.category)) {
      return fail("VALIDATION_ERROR", "기록 카테고리와 내용을 입력해주세요.");
    }

    const structured = await createPetLogStructuredRecord({ fallbackCategory: body.category, detail: body.detail });
    const record = updateMockRecord(path[1], { category: body.category, detail: body.detail, structured });
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

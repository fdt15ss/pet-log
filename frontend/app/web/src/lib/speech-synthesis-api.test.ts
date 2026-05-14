import { strict as assert } from "node:assert";
import test from "node:test";
import { POST } from "../app/api/v1/[...path]/route";
import { restoreEnvValue } from "./sprint-test-utils";

test("음성 합성 API는 text JSON을 FastAPI synthesis endpoint로 프록시하고 audio를 반환한다", async () => {
  const previousBaseUrl = process.env.PET_LOG_BACKEND_API_BASE_URL;
  const previousFetch = global.fetch;
  process.env.PET_LOG_BACKEND_API_BASE_URL = "http://127.0.0.1:27893";

  global.fetch = (async (input: string | URL | Request, init?: RequestInit) => {
    assert.equal(String(input), "http://127.0.0.1:27893/api/v1/speech/synthesis");
    assert.equal(init?.method, "POST");
    assert.equal(init?.headers && (init.headers as Record<string, string>)["Content-Type"], "application/json");
    assert.deepEqual(JSON.parse(String(init?.body)), {
      text: "주의 기록 후속 확인이 필요합니다.",
      voice: "ko-KR-InJoonNeural",
    });

    return new Response(new Uint8Array([1, 2, 3]), {
      headers: { "Content-Type": "audio/mpeg" },
      status: 200,
    });
  }) as typeof fetch;

  try {
    const response = await POST(
      new Request("http://localhost/api/v1/speech/synthesis", {
        body: JSON.stringify({ text: "주의 기록 후속 확인이 필요합니다.", voice: "ko-KR-InJoonNeural" }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      }) as never,
      { params: Promise.resolve({ path: ["speech", "synthesis"] }) },
    );

    assert.equal(response.status, 200);
    assert.equal(response.headers.get("content-type"), "audio/mpeg");
    assert.deepEqual(new Uint8Array(await response.arrayBuffer()), new Uint8Array([1, 2, 3]));
  } finally {
    global.fetch = previousFetch;
    restoreEnvValue("PET_LOG_BACKEND_API_BASE_URL", previousBaseUrl);
  }
});

test("음성 합성 API는 FastAPI synthesis 실패를 공통 실패 응답으로 반환한다", async () => {
  const previousBaseUrl = process.env.PET_LOG_BACKEND_API_BASE_URL;
  const previousFetch = global.fetch;
  process.env.PET_LOG_BACKEND_API_BASE_URL = "http://127.0.0.1:27893";

  global.fetch = (async () =>
    new Response(JSON.stringify({ detail: "text must not be empty" }), {
      headers: { "Content-Type": "application/json" },
      status: 422,
    })) as typeof fetch;

  try {
    const response = await POST(
      new Request("http://localhost/api/v1/speech/synthesis", {
        body: JSON.stringify({ text: "" }),
        headers: { "Content-Type": "application/json" },
        method: "POST",
      }) as never,
      { params: Promise.resolve({ path: ["speech", "synthesis"] }) },
    );
    const json = await response.json();

    assert.equal(response.status, 422);
    assert.deepEqual(json, {
      ok: false,
      error: {
        code: "SPEECH_SYNTHESIS_FAILED",
        message: "text must not be empty",
      },
    });
  } finally {
    global.fetch = previousFetch;
    restoreEnvValue("PET_LOG_BACKEND_API_BASE_URL", previousBaseUrl);
  }
});

import { strict as assert } from "node:assert";
import test from "node:test";
import { POST } from "../app/api/v1/[...path]/route";
import { restoreEnvValue } from "./sprint-test-utils";

test("음성 입력 API는 multipart audio를 FastAPI transcription endpoint로 프록시한다", async () => {
  const previousBaseUrl = process.env.PET_LOG_BACKEND_API_BASE_URL;
  const previousFetch = global.fetch;
  process.env.PET_LOG_BACKEND_API_BASE_URL = "http://127.0.0.1:8000";

  global.fetch = (async (input: string | URL | Request, init?: RequestInit) => {
    assert.equal(String(input), "http://127.0.0.1:8000/api/v1/speech/transcriptions");
    assert.equal(init?.method, "POST");
    assert.ok(init?.body instanceof FormData);
    const forwardedAudio = init.body.get("audio");
    assert.ok(forwardedAudio instanceof File);
    assert.equal(forwardedAudio.name, "recording.webm");
    assert.equal(forwardedAudio.type, "audio/webm");

    return new Response(JSON.stringify({ success: true, data: { text: "오늘 아침 사료를 먹었어" } }), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    });
  }) as typeof fetch;

  try {
    const body = new FormData();
    body.set("audio", new File([new Uint8Array([1, 2, 3])], "recording.webm", { type: "audio/webm" }));

    const response = await POST(
      new Request("http://localhost/api/v1/speech/transcriptions", {
        body,
        method: "POST",
      }) as never,
      { params: Promise.resolve({ path: ["speech", "transcriptions"] }) },
    );
    const json = await response.json();

    assert.equal(response.status, 200);
    assert.deepEqual(json, { ok: true, data: { text: "오늘 아침 사료를 먹었어" } });
  } finally {
    global.fetch = previousFetch;
    restoreEnvValue("PET_LOG_BACKEND_API_BASE_URL", previousBaseUrl);
  }
});

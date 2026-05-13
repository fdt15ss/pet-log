import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import test from "node:test";

const recordPageSource = readFileSync(new URL("../app/record/page.tsx", import.meta.url), "utf8");

test("기록 화면은 등록된 pet이 없으면 AI 미리보기와 저장 API를 호출하지 않는다", () => {
  assert.ok(recordPageSource.includes("const hasActivePet = !!profile.id"));
  assert.ok(recordPageSource.includes("if (!hasActivePet)"));
  assert.ok(recordPageSource.includes("반려동물을 먼저 등록해주세요."));
  assert.ok(recordPageSource.includes("isSaving || isInvalid || needsVoiceConfirmation || !hasActivePet"));
});

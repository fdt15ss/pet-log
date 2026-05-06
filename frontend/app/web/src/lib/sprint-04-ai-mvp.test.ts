import { strict as assert } from "node:assert";
import test from "node:test";
import { getAiCareSuggestions, structureRecord } from "./ai-insights";
import { records } from "./mock-data";

test("스프린트 4: AI 기록 구조화와 안전 제안 문구를 유지한다", () => {
  const structured = structureRecord("아침 사료 45g 먹고 산책 20분 했어요.", "meal");
  const suggestions = getAiCareSuggestions([
    {
      ...records[0],
      category: "behavior",
      status: "alert",
      title: "현관 앞 불안",
      detail: "낑낑거림이 반복됨",
    },
  ]);

  assert.equal(structured.suggestedCategory, "meal");
  assert.deepEqual(
    structured.measurements.map((measurement) => measurement.value),
    ["45g", "20분"],
  );
  assert.ok(suggestions.some((suggestion) => suggestion.detail.includes("진단이 아닙니다")));
});

test("스프린트 4 엣지: 키워드가 부족하면 fallback 분류와 확인 필요 상태를 유지한다", () => {
  const structured = structureRecord("평소와 조금 달라 보여요", "medical");

  assert.equal(structured.suggestedCategory, "medical");
  assert.equal(structured.needsConfirmation, true);
  assert.deepEqual(structured.measurements, []);
});

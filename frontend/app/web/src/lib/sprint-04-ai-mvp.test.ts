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

test("전체 기본 분류는 식사 자연어를 식사로 자동 인식한다", () => {
  const structured = structureRecord("아침에 밥을 천천히 먹었어", "all");

  assert.equal(structured.suggestedCategory, "meal");
  assert.equal(structured.needsConfirmation, false);
});

test("복합 일상 기록은 문장에 포함된 카테고리들을 함께 감지한다", () => {
  const structured = structureRecord(
    "아침 사료는 평소 양의 80% 정도 먹었고, 저녁 산책은 30분 다녀왔으며, 병원 방문은 없었고, 배변은 정상 변 1회, 행동은 평소보다 조금 조용하고 몸무게는 정상",
    "all",
  );

  assert.deepEqual(structured.detectedCategories, ["meal", "walk", "medical", "stool", "behavior"]);
  assert.equal(structured.suggestedCategory, "meal");
  assert.equal(structured.needsConfirmation, false);
  assert.deepEqual(
    structured.measurements.map((measurement) => measurement.value),
    ["80%", "30분", "1회"],
  );
});

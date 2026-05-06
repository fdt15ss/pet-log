import { strict as assert } from "node:assert";
import test from "node:test";
import { structureRecord } from "./ai-insights";
import { createMockRecord, getMockPetLogSnapshot, resetMockPetLogSnapshot } from "./server/mock-pet-log-store";
import { getTimelineRecords } from "./timeline";

test("스프린트 1: 기록 입력은 세션 스냅샷과 타임라인 검색에 연결된다", () => {
  resetMockPetLogSnapshot();
  const beforeCount = getMockPetLogSnapshot().records.length;
  const detail = "아침 사료 45g 먹었어요.";
  const created = createMockRecord({
    category: "meal",
    detail,
    structured: structureRecord(detail, "meal"),
  });
  const snapshot = getMockPetLogSnapshot();
  const visibleRecords = getTimelineRecords(snapshot.records, { filter: "all", query: "45g" });

  assert.equal(snapshot.records.length, beforeCount + 1);
  assert.equal(snapshot.records[0]?.id, created.id);
  assert.equal(visibleRecords[0]?.id, created.id);
});

test("스프린트 1 엣지: 빈 검색어는 전체 기록을 유지하고 없는 검색어는 빈 목록을 반환한다", () => {
  resetMockPetLogSnapshot();
  const snapshot = getMockPetLogSnapshot();

  assert.equal(getTimelineRecords(snapshot.records, { filter: "all", query: "" }).length, snapshot.records.length);
  assert.deepEqual(getTimelineRecords(snapshot.records, { filter: "all", query: "없는기록키워드" }), []);
});

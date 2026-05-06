import { strict as assert } from "node:assert";
import test from "node:test";
import {
  appendMockChatbotExchange,
  getMockChatbotThreads,
  getMockPetLogSnapshot,
  resetMockPetLogSnapshot,
  updateMockReadNotifications,
} from "./server/mock-pet-log-store";

test("스프린트 13: mock API 전환용 서버 스냅샷은 앱 초기 상태와 읽음 상태를 제공한다", () => {
  resetMockPetLogSnapshot();
  const snapshot = getMockPetLogSnapshot();
  const readIds = updateMockReadNotifications(["missing-stool", "missing-stool", 1 as unknown as string]);

  assert.equal(snapshot.version, 1);
  assert.ok(snapshot.records.length > 0);
  assert.ok(snapshot.schedules.length > 0);
  assert.deepEqual(readIds, ["missing-stool"]);
});

test("스프린트 13 엣지: 스냅샷 reset은 챗봇 대화 이력도 초기화한다", () => {
  appendMockChatbotExchange(undefined, "질문", {
    answer: "답변",
    referencedRecordIds: [],
    safetyNotice: "진단이 아닙니다.",
  });
  resetMockPetLogSnapshot();

  assert.deepEqual(getMockChatbotThreads(), []);
});

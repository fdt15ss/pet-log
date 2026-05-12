import { readFileSync } from "node:fs";
import { test } from "node:test";
import assert from "node:assert/strict";

const providerSource = readFileSync(new URL("../components/pet-log-provider.tsx", import.meta.url), "utf8");

test("PetLogProvider는 기록 화면에 mock 기록을 폴백으로 보여주지 않는다", () => {
  assert.equal(providerSource.includes("records as initialRecords"), false);
  assert.equal(providerSource.includes("setRecords(initialRecords)"), false);
  assert.equal(providerSource.includes("로컬 데모 상태"), false);
  assert.equal(providerSource.includes("로컬 예시 데이터"), false);
});

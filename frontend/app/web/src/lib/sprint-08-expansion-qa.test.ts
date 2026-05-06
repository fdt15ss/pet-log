import { strict as assert } from "node:assert";
import { existsSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import { toggleSavedRecommendation } from "./expansion-state";

test("스프린트 8: 확장 화면 라우트와 저장 토글 유틸이 유지된다", () => {
  const routeFiles = ["shared-care", "hospital", "shopping"].map((route) => `src/app/${route}/page.tsx`);
  const saved = toggleSavedRecommendation([], "health-basic");

  assert.ok(routeFiles.every((path) => existsSync(join(process.cwd(), path))));
  assert.deepEqual(saved, ["health-basic"]);
});

test("스프린트 8 엣지: 이미 저장한 추천을 다시 토글하면 제거된다", () => {
  const saved = toggleSavedRecommendation(["health-basic"], "health-basic");

  assert.deepEqual(saved, []);
});

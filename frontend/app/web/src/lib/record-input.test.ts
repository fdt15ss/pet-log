import { strict as assert } from "node:assert";
import { getInputModeFeedback, recordInputFlow } from "./record-input";

assert.deepEqual(recordInputFlow, ["category", "mode", "entry", "ai-preview", "recent-records"]);

const textMode = getInputModeFeedback("text");
assert.equal(textMode.status, "available");
assert.ok(textMode.detail.includes("자연어"));

const voiceMode = getInputModeFeedback("voice");
assert.equal(voiceMode.status, "coming-soon");
assert.ok(voiceMode.detail.includes("준비 중"));

const photoMode = getInputModeFeedback("photo");
assert.equal(photoMode.status, "coming-soon");
assert.ok(photoMode.detail.includes("메모"));

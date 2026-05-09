import { strict as assert } from "node:assert";
import {
  defaultRecordCategoryChoice,
  getBrowserSpeechRecognitionConstructor,
  getInputModeFeedback,
  getRecordCategoryChoiceLabel,
  recordCategoryChoiceOptions,
  recordInputFlow,
  resolveRecordCategoryForSave,
  type BrowserSpeechRecognition,
} from "./record-input";

assert.deepEqual(recordInputFlow, ["category", "mode", "entry", "ai-preview", "recent-records"]);
assert.equal(defaultRecordCategoryChoice, "all");
assert.deepEqual(
  recordCategoryChoiceOptions.slice(0, 2).map((option) => [option.label, option.value]),
  [
    ["AI 자동", "all"],
    ["식사", "meal"],
  ],
);
assert.equal(getRecordCategoryChoiceLabel("all"), "AI 자동");
assert.equal(getRecordCategoryChoiceLabel("walk"), "산책");
assert.equal(
  resolveRecordCategoryForSave("all", {
    sourceText: "아침 사료를 먹었어",
    normalizedSummary: "아침 식사",
    suggestedCategory: "meal",
    confidence: 0.86,
    measurements: [],
    needsConfirmation: false,
  }),
  "meal",
);
assert.equal(
  resolveRecordCategoryForSave("walk", {
    sourceText: "아침 사료를 먹었어",
    normalizedSummary: "아침 식사",
    suggestedCategory: "meal",
    confidence: 0.86,
    measurements: [],
    needsConfirmation: false,
  }),
  "walk",
);

const textMode = getInputModeFeedback("text");
assert.equal(textMode.status, "available");
assert.ok(textMode.detail.includes("자연어"));

const voiceMode = getInputModeFeedback("voice");
assert.equal(voiceMode.status, "available");
assert.equal(voiceMode.label, "녹음");
assert.ok(voiceMode.detail.includes("마이크"));

const photoMode = getInputModeFeedback("photo");
assert.equal(photoMode.status, "coming-soon");
assert.ok(photoMode.detail.includes("메모"));

class NativeSpeechRecognition implements BrowserSpeechRecognition {
  continuous = false;
  interimResults = false;
  lang = "";
  onend = null;
  onerror = null;
  onresult = null;
  start() {}
  stop() {}
}

class WebkitSpeechRecognition extends NativeSpeechRecognition {}

assert.equal(
  getBrowserSpeechRecognitionConstructor({
    SpeechRecognition: NativeSpeechRecognition,
    webkitSpeechRecognition: WebkitSpeechRecognition,
  }),
  NativeSpeechRecognition,
);
assert.equal(getBrowserSpeechRecognitionConstructor({ webkitSpeechRecognition: WebkitSpeechRecognition }), WebkitSpeechRecognition);
assert.equal(getBrowserSpeechRecognitionConstructor({}), null);

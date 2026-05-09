import { strict as assert } from "node:assert";
import { getBrowserSpeechRecognitionConstructor, getInputModeFeedback, recordInputFlow, type BrowserSpeechRecognition } from "./record-input";

assert.deepEqual(recordInputFlow, ["category", "mode", "entry", "ai-preview", "recent-records"]);

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

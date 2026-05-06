import { strict as assert } from "node:assert";
import { createPetLogStructuredRecord } from "./pet-log-ai-service";

(async () => {
  const structured = await createPetLogStructuredRecord({
    detail: "아침 사료 45g 먹고 산책 20분 했어요.",
    fallbackCategory: "meal",
  });

  assert.equal(structured.sourceText, "아침 사료 45g 먹고 산책 20분 했어요.");
  assert.equal(structured.suggestedCategory, "meal");
  assert.equal(structured.measurements[0]?.label, "급여량");
  assert.equal(structured.measurements[0]?.value, "45g");
  assert.equal(structured.measurements[1]?.label, "시간");
  assert.equal(structured.measurements[1]?.value, "20분");
  assert.equal(structured.needsConfirmation, false);
})();

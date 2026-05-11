import { strict as assert } from "node:assert";
import test, { mock } from "node:test";
import { apiClient, fetchAiInsights, fetchAiSuggestions, structureRecordPreview } from "./api-client";

test("fetchAiInsights returns insights from API", async () => {
  const mockInsights = [
    { severity: "info", title: "Test Insight", reason: "Test Reason", sourceRecordIds: ["rec-1"] }
  ];

  const getMock = mock.method(apiClient, "get", async () => {
    return {
      data: {
        ok: true,
        data: { insights: mockInsights }
      }
    };
  });

  try {
    const result = await fetchAiInsights("pet-123");
    assert.deepEqual(result.insights, mockInsights);
    assert.equal(getMock.mock.callCount(), 1);
    const firstCall = getMock.mock.calls[0];
    assert.equal(firstCall.arguments[0], "/ai/insights");
    assert.deepEqual((firstCall.arguments[1] as { params: object }).params, { pet_id: "pet-123" });
  } finally {
    getMock.mock.restore();
  }
});

test("fetchAiSuggestions returns suggestions from API", async () => {
  const mockSuggestions = [
    { title: "Test Suggestion", action: "Test Action", reason: "Test Reason", sourceRecordIds: ["rec-2"] }
  ];

  const getMock = mock.method(apiClient, "get", async () => {
    return {
      data: {
        ok: true,
        data: { suggestions: mockSuggestions }
      }
    };
  });

  try {
    const result = await fetchAiSuggestions("pet-123");
    assert.deepEqual(result.suggestions, mockSuggestions);
    assert.equal(getMock.mock.callCount(), 1);
    const firstCall = getMock.mock.calls[0];
    assert.equal(firstCall.arguments[0], "/ai/suggestions");
    assert.deepEqual((firstCall.arguments[1] as { params: object }).params, { pet_id: "pet-123" });
  } finally {
    getMock.mock.restore();
  }
});

test("structureRecordPreview returns structured record with candidates", async () => {
  const mockStructured = {
    sourceText: "test",
    normalizedSummary: "test",
    suggestedCategory: "meal",
    confidence: 0.9,
    measurements: [],
    needsConfirmation: false,
    candidates: [
      {
        title: "Candidate 1",
        detail: "Detail 1",
        category: "meal",
        status: "normal",
        confidence: 0.9,
        needsConfirmation: false
      }
    ]
  };

  const postMock = mock.method(apiClient, "post", async () => {
    return {
      data: {
        ok: true,
        data: { structured: mockStructured }
      }
    };
  });

  try {
    const result = await structureRecordPreview({ detail: "test", fallbackCategory: "meal" });
    assert.deepEqual(result.structured, mockStructured);
    assert.equal(result.structured.candidates?.length, 1);
    assert.equal(postMock.mock.callCount(), 1);
  } finally {
    postMock.mock.restore();
  }
});

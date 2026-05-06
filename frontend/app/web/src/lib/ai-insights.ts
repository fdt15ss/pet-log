import type { ExtractedMeasurement, RecordCategory, RecordEntry, StructuredRecord, SuggestionCategory, SuggestionTone } from "./types";

type AiCareSuggestion = {
  id: string;
  category: SuggestionCategory;
  title: string;
  detail: string;
  action: string;
  actionHref: string;
  tone: SuggestionTone;
};

type AiInsight = {
  id: string;
  title: string;
  detail: string;
  tone: "green" | "orange" | "red";
};

const categoryKeywords: Record<RecordCategory, string[]> = {
  meal: ["사료", "밥", "먹", "간식", "급여", "g"],
  walk: ["산책", "걷", "활동", "운동", "분"],
  stool: ["배변", "소변", "대변", "변", "설사", "토"],
  medical: ["병원", "약", "접종", "백신", "진료", "복용"],
  behavior: ["불안", "짖", "낑낑", "기다림", "흥분", "행동"],
};

const measurementLabels: Record<string, string> = {
  g: "급여량",
  kg: "체중",
  분: "시간",
  회: "횟수",
};

export function structureRecord(detail: string, fallbackCategory: RecordCategory): StructuredRecord {
  const sourceText = detail.trim();
  const matched = Object.entries(categoryKeywords)
    .map(([category, keywords]) => ({
      category: category as RecordCategory,
      score: keywords.filter((keyword) => sourceText.includes(keyword)).length,
    }))
    .sort((a, b) => b.score - a.score);

  const bestMatch = matched[0];
  const suggestedCategory = bestMatch && bestMatch.score > 0 ? bestMatch.category : fallbackCategory;
  const confidence = bestMatch?.score
    ? Math.min(0.92, 0.54 + bestMatch.score * 0.14 + (suggestedCategory === fallbackCategory ? 0.1 : 0))
    : 0.42;

  return {
    sourceText,
    normalizedSummary: createNormalizedSummary(sourceText),
    suggestedCategory,
    confidence,
    measurements: extractMeasurements(sourceText),
    needsConfirmation: confidence < 0.7 || suggestedCategory !== fallbackCategory,
  };
}

export function getAiInsights(records: RecordEntry[]): AiInsight[] {
  const recentRecords = records.slice(0, 7);
  const insights: AiInsight[] = [];

  if (!recentRecords.some((record) => record.category === "stool")) {
    insights.push({
      id: "missing-stool",
      title: "배변 기록 확인이 필요합니다",
      detail: "최근 기록에서 배변 상태가 보이지 않습니다. 변화 판단을 위해 오늘 상태를 한 번 남겨보세요.",
      tone: "orange",
    });
  }

  if (!recentRecords.some((record) => record.category === "walk")) {
    insights.push({
      id: "missing-walk",
      title: "활동 기록이 비어 있습니다",
      detail: "산책이나 놀이 기록이 없으면 활동 리듬을 판단하기 어렵습니다. 짧은 활동도 기록해보세요.",
      tone: "orange",
    });
  }

  const alertRecord = recentRecords.find((record) => record.status === "alert");
  if (alertRecord) {
    insights.push({
      id: "alert-pattern",
      title: "주의 기록이 포함되어 있습니다",
      detail: `${alertRecord.title} 기록이 있습니다. 같은 변화가 반복되거나 심해지면 병원 상담을 권장합니다.`,
      tone: "red",
    });
  }

  if (insights.length === 0) {
    insights.push({
      id: "stable",
      title: "최근 기록은 안정적으로 보입니다",
      detail: "식사, 활동, 배변 기록이 모두 확인됩니다. 지금처럼 짧게라도 꾸준히 남기면 변화 판단에 도움이 됩니다.",
      tone: "green",
    });
  }

  return insights;
}

export function getAiCareSuggestions(records: RecordEntry[]): AiCareSuggestion[] {
  const insights = getAiInsights(records);
  return insights.map((insight, index) => {
    if (insight.id === "missing-stool") {
      return {
        id: "ai-stool",
        category: "건강",
        title: "배변 상태를 먼저 확인해보세요",
        detail: "배변 기록이 비어 있으면 컨디션 변화를 놓칠 수 있습니다. 색, 형태, 횟수를 짧게 남겨보세요.",
        action: "기록하기",
        actionHref: "/record",
        tone: "orange",
      };
    }

    if (insight.id === "missing-walk") {
      return {
        id: "ai-walk",
        category: "생활",
        title: "짧은 활동 기록을 추가해보세요",
        detail: "활동량은 식사와 행동 변화 해석에 같이 쓰입니다. 산책이 어렵다면 실내 놀이 시간도 기록해보세요.",
        action: "기록하기",
        actionHref: "/record",
        tone: "green",
      };
    }

    if (insight.id === "alert-pattern") {
      return {
        id: "ai-alert",
        category: "건강",
        title: "주의 기록을 이어서 관찰하세요",
        detail: "이 제안은 진단이 아닙니다. 비슷한 상태가 반복되거나 심해지면 기록을 모아 병원 상담을 권장합니다.",
        action: "타임라인 보기",
        actionHref: "/timeline",
        tone: "orange",
      };
    }

    return {
      id: `ai-stable-${index}`,
      category: "생활",
      title: "현재 기록 리듬을 유지해보세요",
      detail: "최근 주요 기록이 고르게 남아 있습니다. 같은 방식으로 기록을 이어가면 주간 변화 확인이 쉬워집니다.",
      action: "분석 보기",
      actionHref: "/analysis",
      tone: "blue",
    };
  });
}

function createNormalizedSummary(text: string) {
  if (!text) {
    return "입력된 기록 없음";
  }

  const firstSentence = text.split(/\n|[.!?。]/)[0]?.trim() ?? text;
  return firstSentence.length > 38 ? `${firstSentence.slice(0, 38)}...` : firstSentence;
}

function extractMeasurements(text: string): ExtractedMeasurement[] {
  const matches = text.match(/\d+(?:\.\d+)?\s?(?:g|kg|분|회)/g) ?? [];
  return matches.slice(0, 4).map((value) => {
    const unit = value.replace(/[\d.\s]/g, "");
    return {
      label: measurementLabels[unit] ?? "수치",
      value,
    };
  });
}

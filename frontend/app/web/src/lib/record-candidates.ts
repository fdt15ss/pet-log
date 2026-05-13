import type { ExtractedMeasurement, RecordCategory, StructuredRecord, StructuredRecordCandidate } from "./types";

const categoryTitles: Record<RecordCategory, string> = {
  meal: "식사",
  walk: "산책",
  stool: "배변",
  medical: "병원/약",
  behavior: "행동",
};

const categoryMeasurementLabels: Record<RecordCategory, string[]> = {
  meal: ["급여량", "섭취량", "사료", "비율"],
  walk: ["시간", "산책 시간", "소요 시간", "거리"],
  stool: ["횟수", "소변", "대변", "배변", "내용"],
  medical: ["횟수", "체중", "부위", "증상", "진료", "내용"],
  behavior: ["횟수", "시간", "행동", "반응", "내용"],
};

const categoryDetailKeywords: Record<RecordCategory, string[]> = {
  meal: ["사료", "밥", "먹", "급여", "간식", "g", "kg", "그램"],
  walk: ["산책", "걷", "운동", "돌아", "시간", "분"],
  stool: ["소변", "대변", "배변", "변", "오줌", "응가"],
  medical: ["병원", "약", "접종", "진료", "검진", "처방", "상처", "피", "구토", "설사", "긁"],
  behavior: ["불안", "짖", "무서워", "겁", "낑낑", "흥분", "행동", "반응", "예민"],
};

export function buildConfirmedRecordCandidates(structured: StructuredRecord): StructuredRecordCandidate[] {
  const categories = uniqueCategories(
    structured.detectedCategories?.length ? structured.detectedCategories : [structured.suggestedCategory],
  );

  return categories.map((category) => {
    const pickedMeasurements = pickMeasurementsForCategory(structured.measurements, category);
    const inferredMeasurements = inferMeasurementsForCategory(structured.sourceText, category);
    const measurements = pickedMeasurements.length > 0 ? pickedMeasurements : inferredMeasurements;
    const detail = createCandidateDetail(structured.sourceText, category, measurements);

    return {
      title: category === structured.suggestedCategory ? createCandidateTitle(structured, category, detail) : categoryTitles[category],
      detail,
      category,
      status: "normal",
      confidence: structured.confidence,
      needsConfirmation: structured.needsConfirmation,
      measurements,
    };
  });
}

export function refineRecordCandidateDetails(sourceText: string, candidates: StructuredRecordCandidate[]) {
  return candidates.map((candidate) => {
    const candidateMeasurements = candidate.measurements ?? [];
    const refinedMeasurements =
      candidateMeasurements.length > 0
        ? candidateMeasurements
        : inferMeasurementsForCategory(sourceText, candidate.category);

    const detail = createCandidateDetail(sourceText, candidate.category, refinedMeasurements);

    if (!detail || detail === sourceText) {
      return { ...candidate, measurements: refinedMeasurements };
    }

    return {
      ...candidate,
      detail,
      measurements: refinedMeasurements,
    };
  });
}

function uniqueCategories(categories: RecordCategory[]) {
  return categories.filter((category, index) => categories.indexOf(category) === index);
}

function pickMeasurementsForCategory(measurements: ExtractedMeasurement[], category: RecordCategory) {
  const labels = categoryMeasurementLabels[category];

  return measurements.filter(
    (measurement) =>
      labels.includes(measurement.label) ||
      labels.some((label) => measurement.label.includes(label)),
  );
}

function inferMeasurementsForCategory(sourceText: string, category: RecordCategory): ExtractedMeasurement[] {
  const text = normalizeText(sourceText);

  if (!text) {
    return [];
  }

  if (category === "meal") {
    const amount =
      text.match(/(?:사료|밥|간식|급여).{0,16}?(\d+(?:\.\d+)?\s*(?:g|kg|그램|킬로))/u)?.[1] ??
      text.match(/(\d+(?:\.\d+)?\s*(?:g|kg|그램|킬로)).{0,16}?(?:사료|밥|간식|먹|급여)/u)?.[1];

    return amount ? [{ label: "급여량", value: normalizeValue(amount) }] : [];
  }

  if (category === "walk") {
    const duration =
      text.match(/산책.{0,20}?(\d+(?:\.\d+)?\s*(?:시간|분))/u)?.[1] ??
      text.match(/(\d+(?:\.\d+)?\s*(?:시간|분)).{0,20}?산책/u)?.[1];

    return duration ? [{ label: "시간", value: normalizeValue(duration) }] : [];
  }

  if (category === "stool") {
    const stoolType = extractStoolTypePhrase(text);
    return stoolType ? [{ label: "배변", value: stoolType }] : [];
  }

  if (category === "medical") {
    const detail = extractMedicalDetailPhrase(text);
    return detail ? [{ label: "내용", value: detail }] : [];
  }

  if (category === "behavior") {
    const detail = extractBehaviorDetailPhrase(text);
    return detail ? [{ label: "반응", value: detail }] : [];
  }

  return [];
}

function createCandidateTitle(structured: StructuredRecord, category: RecordCategory, detail: string) {
  if (detail && detail !== structured.sourceText) {
    return categoryTitles[category];
  }

  return structured.normalizedSummary || categoryTitles[category];
}

function createCandidateDetail(sourceText: string, category: RecordCategory, measurements: ExtractedMeasurement[]) {
  const text = normalizeText(sourceText);

  if (!text) {
    return sourceText;
  }

  const ruleDetail = createRuleBasedDetail(text, category, measurements);

  if (ruleDetail) {
    return ruleDetail;
  }

  return extractBestSegment(text, category) ?? sourceText;
}

function createRuleBasedDetail(text: string, category: RecordCategory, measurements: ExtractedMeasurement[]) {
  const time = extractTimePhrase(text);
  const values = measurements.map((measurement) => measurement.value);

  if (category === "meal" && /사료|밥|간식|먹|급여/.test(text)) {
    const food = text.match(/사료|밥|간식|습식|건식/)?.[0] ?? "식사";
    const amount =
      values.find((value) => /g|kg|그램|킬로|%/.test(value)) ??
      text.match(/(?:사료|밥|간식|급여).{0,16}?(\d+(?:\.\d+)?\s*(?:g|kg|그램|킬로))/u)?.[1] ??
      text.match(/(\d+(?:\.\d+)?\s*(?:g|kg|그램|킬로)).{0,16}?(?:사료|밥|간식|먹|급여)/u)?.[1];

    return compactJoin([time, compactJoin([food, amount ? normalizeValue(amount) : "", "섭취"])]);
  }

  if (category === "walk" && /산책|걷|운동/.test(text)) {
    const duration =
      values.find((value) => /시간|분/.test(value)) ??
      text.match(/산책.{0,20}?(\d+(?:\.\d+)?\s*(?:시간|분))/u)?.[1] ??
      text.match(/(\d+(?:\.\d+)?\s*(?:시간|분)).{0,20}?산책/u)?.[1];

    return compactJoin([time, compactJoin(["산책", duration ? normalizeValue(duration) : ""])]);
  }

  if (category === "stool" && /소변|대변|배변|오줌|응가|변/.test(text)) {
    const stoolType = extractStoolTypePhrase(text);
    const context = /산책.{0,12}(중|동안)/.test(text) || /산책하는 동안/.test(text) ? "산책 중" : "";
    return compactJoin([context, stoolType]);
  }

  if (category === "medical" && /병원|약|접종|진료|검진|처방|복용|수술|상처|손톱|발톱|구토|설사|피|긁|핥|아프|다치/.test(text)) {
    return extractMedicalDetailPhrase(text);
  }

  if (category === "behavior" && /무서워|겁|불안|떨|긴장|짖|흥분|기다|반응|예민|낑낑/.test(text)) {
    return extractBehaviorDetailPhrase(text);
  }

  return "";
}

function extractStoolTypePhrase(text: string) {
  const types: string[] = [];

  if (/소변|오줌/.test(text)) {
    types.push("소변");
  }

  if (/대변|응가/.test(text)) {
    types.push("대변");
  }

  if (types.length === 0 && /배변|변/.test(text)) {
    types.push("배변");
  }

  return types.join("과 ") || "배변";
}

function extractTimePhrase(text: string) {
  return (
    text.match(
      /오늘\s*(?:아침|점심|저녁)?\s*\d{1,2}시(?:\s*\d{1,2}분)?|(?:아침|점심|저녁)\s*\d{1,2}시(?:\s*\d{1,2}분)?/u,
    )?.[0] ?? ""
  );
}

function extractMedicalDetailPhrase(text: string) {
  const injuryWithBleedingCare = text.match(
    /(?:머리|귀|눈|코|입|피부|배|등|다리|발|손|손발|손톱|발톱)(?:를|을|가|에)?\s*(?:긁|핥|다치|아프).{0,36}?(?:피|상처).{0,36}?(?:병원|진료|검진|처방).{0,24}?(?:받았어|받았|받음|다녀왔|갔|방문)/u,
  );

  if (injuryWithBleedingCare) {
    return injuryWithBleedingCare[0].trim();
  }

  const injuryCare = text.match(
    /(?:머리|귀|눈|코|입|피부|배|등|다리|발|손|손발|손톱|발톱).{0,36}?(?:피|상처|긁|핥|아프|다치|염증).{0,36}?(?:병원|진료|검진|처방).{0,24}?(?:받았|받음|다녀왔|갔|방문)/u,
  );

  if (injuryCare) {
    return injuryCare[0].trim();
  }

  const detail = extractContextPhrase(text, /병원|약|접종|진료|검진|처방|복용|수술|상처|손톱|발톱|구토|설사|피|긁|핥|아프|다치/u, {
    endBoundaries: [" 병원에서 ", " 진료를 받는데 ", " 집에서 ", " 그리고 ", " 그 후 ", " 이후 ", " 또 ", ". ", "! ", "? ", "。"],
    startBoundaries: [" 쉬는 중에 ", " 집에 와서 ", " 집에서 ", " 그리고 ", " 그 후 ", " 이후 ", " 또 ", ". ", "! ", "? ", "。"],
  });

  return detail.replace(/\s*(?:진료를 받는데|병원에서)\s*(?:무서워|겁|불안|떨|긴장|짖|흥분|예민|낑낑).*/u, "").trim();
}

function extractBehaviorDetailPhrase(text: string) {
  const careBehavior = text.match(
    /(?:진료를 받는데|진료 중|병원에서).{0,48}?(?:무서워|겁|불안|떨|긴장|짖|흥분|예민|낑낑).*/u,
  );

  if (careBehavior) {
    return careBehavior[0].trim();
  }

  return extractContextPhrase(text, /무서워|겁|불안|떨|긴장|짖|흥분|기다|반응|예민|낑낑/u, {
    endBoundaries: [" 그리고 ", " 그 후 ", " 이후 ", " 또 ", ". ", "! ", "? ", "。"],
    startBoundaries: [" 진료를 받는데 ", " 진료 중 ", " 병원에서 ", " 산책 중 ", " 집에서 ", " 집에 와서 ", " 그리고 ", " 그 후 ", " 이후 ", " 또 ", ". ", "! ", "? ", "。"],
  });
}

function extractContextPhrase(
  text: string,
  keywordPattern: RegExp,
  {
    endBoundaries,
    startBoundaries,
  }: {
    endBoundaries: string[];
    startBoundaries: string[];
  },
) {
  const match = text.match(keywordPattern);

  if (!match || match.index === undefined) {
    return "";
  }

  const startBoundary = findLastBoundary(text, startBoundaries, match.index);
  const endBoundary = findFirstBoundary(text, endBoundaries, match.index + match[0].length);
  const start = startBoundary < 0 ? 0 : startBoundary;
  const end = endBoundary < 0 ? text.length : endBoundary;

  return text.slice(start, end).trim();
}

function findLastBoundary(text: string, boundaries: string[], beforeIndex: number) {
  return boundaries.reduce((best, boundary) => {
    const index = text.lastIndexOf(boundary, beforeIndex);

    if (index < 0) {
      return best;
    }

    const start = boundary.startsWith(" ") ? index + 1 : index + boundary.length;

    return start > best ? start : best;
  }, -1);
}

function findFirstBoundary(text: string, boundaries: string[], afterIndex: number) {
  return boundaries.reduce((best, boundary) => {
    const index = text.indexOf(boundary, afterIndex);

    if (index < 0) {
      return best;
    }

    return best < 0 || index < best ? index : best;
  }, -1);
}

function extractBestSegment(text: string, category: RecordCategory) {
  const keywords = categoryDetailKeywords[category];
  const segments = text
    .split(/(?:[.!?。]\s*)|(?:\s+그\s*후\s+)|(?:\s+그리고\s+)|(?:\s+또\s+)|(?:\s+이후\s+)/u)
    .map((segment) => segment.trim())
    .filter(Boolean);

  const best = segments
    .map((segment) => ({
      segment,
      score: keywords.filter((keyword) => segment.includes(keyword)).length,
    }))
    .sort((left, right) => right.score - left.score)[0];

  if (!best || best.score === 0) {
    return null;
  }

  return best.segment.length > 80 ? `${best.segment.slice(0, 80)}...` : best.segment;
}

function compactJoin(parts: Array<string | undefined>) {
  return parts.filter((part): part is string => !!part?.trim()).join(" ");
}

function normalizeText(text: string) {
  return text.replace(/\s+/g, " ").trim();
}

function normalizeValue(value: string) {
  return value.replace(/\s+/g, "");
}

export function structuredFromCandidate(candidate: StructuredRecordCandidate, sourceText: string): StructuredRecord {
  return {
    sourceText,
    normalizedSummary: candidate.title,
    suggestedCategory: candidate.category,
    detectedCategories: [candidate.category],
    confidence: candidate.confidence,
    measurements: candidate.measurements ?? [],
    needsConfirmation: candidate.needsConfirmation,
  };
}

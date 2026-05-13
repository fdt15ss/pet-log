export type ProfileNameSuggestion = {
  from: string;
  to: string;
  suggestedText: string;
};

export type ContextCorrectionSuggestion = {
  from: string;
  to: string;
  reason: string;
  suggestedText: string;
};

export type VoiceTranscriptReview = {
  recognizedText: string;
  confirmedText: string;
  profileNameSuggestion: ProfileNameSuggestion | null;
  contextCorrectionSuggestions: ContextCorrectionSuggestion[];
};

const hangulBase = 0xac00;
const hangulLast = 0xd7a3;
const choseong = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"];
const jungseong = ["ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ", "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ"];
const jongseong = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"];

export function createVoiceTranscriptReview(transcript: string, profileName: string): VoiceTranscriptReview {
  const recognizedText = transcript.trim();
  const normalizedProfileName = profileName.trim();

  return {
    recognizedText,
    confirmedText: recognizedText,
    profileNameSuggestion: findProfileNameSuggestion(recognizedText, normalizedProfileName),
    contextCorrectionSuggestions: findContextCorrectionSuggestions(recognizedText),
  };
}

function findContextCorrectionSuggestions(text: string): ContextCorrectionSuggestion[] {
  const suggestions: ContextCorrectionSuggestion[] = [];

  for (const feedWord of ["서류", "자료", "사로", "사려"]) {
    if (!shouldSuggestFeedCorrection(text, feedWord)) {
      continue;
    }
    suggestions.push({
      from: feedWord,
      to: "사료",
      reason: "30g과 먹었다는 표현이 함께 있어 사료일 가능성이 높아요.",
      suggestedText: text.replace(feedWord, "사료"),
    });
  }

  const walkTimeSuggestion = findSeparatedWalkTimeSuggestion(text);
  if (walkTimeSuggestion) {
    suggestions.push(walkTimeSuggestion);
  }

  const mealUnitSuggestion = findMealUnitSuggestion(text);
  if (mealUnitSuggestion) {
    suggestions.push(mealUnitSuggestion);
  }

  const feedAmountSuggestion = findFeedAmountFromMinuteSuggestion(text);
  if (feedAmountSuggestion) {
    suggestions.push(feedAmountSuggestion);
  }

  const waterAmountSuggestion = findWaterAmountSuggestion(text);
  if (waterAmountSuggestion) {
    suggestions.push(waterAmountSuggestion);
  }

  const stoolSuggestion = findStoolContextSuggestion(text);
  if (stoolSuggestion) {
    suggestions.push(stoolSuggestion);
  }

  return suggestions;
}

function shouldSuggestFeedCorrection(text: string, word: string) {
  if (!text.includes(word)) {
    return false;
  }

  const escapedWord = escapeRegExp(word);
  const documentContext = new RegExp(`${escapedWord}.{0,8}(제출|발급|작성|준비|챙|보관)|(?:제출|발급|작성|준비|챙|보관).{0,8}${escapedWord}`, "u");
  if (documentContext.test(text)) {
    return false;
  }

  const feedContext = new RegExp(`${escapedWord}.{0,12}\\d+(?:\\.\\d+)?\\s?g.{0,12}(먹|급여|밥|식사)|(?:먹|급여|밥|식사).{0,12}${escapedWord}.{0,12}\\d+(?:\\.\\d+)?\\s?g|${escapedWord}.{0,12}(먹|급여|밥|식사)`, "u");
  return feedContext.test(text);
}

function findSeparatedWalkTimeSuggestion(text: string): ContextCorrectionSuggestion | null {
  const match = text.match(/산책.{0,12}(\d+)\s?시\s+간/u);
  if (!match) {
    return null;
  }

  const from = match[0].match(/\d+\s?시\s+간/u)?.[0] ?? "";
  const to = `${match[1]}시간`;
  return {
    from,
    to,
    reason: "산책 시간 문맥에서는 붙여 쓴 시간 표현이 더 자연스러워요.",
    suggestedText: text.replace(from, to),
  };
}

function findMealUnitSuggestion(text: string): ContextCorrectionSuggestion | null {
  const mealContext = /밥|사료|간식|먹|급여|식사/u;
  const match = text.match(/(\d+(?:\.\d+)?)\s?kg/u);
  if (!match || !mealContext.test(text)) {
    return null;
  }

  const numericValue = Number(match[1]);
  if (!Number.isFinite(numericValue) || numericValue < 1) {
    return null;
  }

  const from = match[0];
  const to = `${match[1]}g`;
  return {
    from,
    to,
    reason: `식사량으로 ${from}은 너무 커 보여 ${to}을 의도했는지 확인이 필요해요.`,
    suggestedText: text.replace(from, to),
  };
}

function findFeedAmountFromMinuteSuggestion(text: string): ContextCorrectionSuggestion | null {
  const match = text.match(/(\d+)\s?분\s*정도[에의]?\s*(사료|밥|간식).{0,12}(먹|급여)/u);
  if (!match) {
    return null;
  }

  const feedWord = match[2];
  const from = match[0].match(/\d+\s?분\s*정도[에의]?\s*(?:사료|밥|간식)/u)?.[0] ?? "";
  const to = `${match[1]}g 정도의 ${feedWord}`;

  return {
    from,
    to,
    reason: "사료를 먹은 문맥에서는 시간이 아니라 급여량 g일 가능성이 높아요.",
    suggestedText: text.replace(from, to),
  };
}

function findWaterAmountSuggestion(text: string): ContextCorrectionSuggestion | null {
  const match = text.match(/물.{0,8}(\d+(?:\.\d+)?)\s?m(?!l).{0,12}(마시|먹)/u);
  if (!match) {
    return null;
  }

  const from = match[0].match(/\d+(?:\.\d+)?\s?m(?!l)/u)?.[0] ?? "";
  const normalizedNumber = from.replace(/\s?m$/u, "");
  const to = `${normalizedNumber}ml`;

  return {
    from,
    to,
    reason: "물을 마신 문맥에서는 거리 m보다 용량 ml일 가능성이 높아요.",
    suggestedText: text.replace(from, to),
  };
}

function findStoolContextSuggestion(text: string): ContextCorrectionSuggestion | null {
  if (!text.includes("대소변")) {
    return null;
  }

  return {
    from: "대소변",
    to: "소변과 대변",
    reason: "대소변은 소변과 대변을 함께 의미해서 기록을 나누기 쉽게 풀어쓸 수 있어요.",
    suggestedText: text.replace("대소변", "소변과 대변"),
  };
}

function escapeRegExp(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function findProfileNameSuggestion(text: string, profileName: string): ProfileNameSuggestion | null {
  if (!text || !profileName || text.includes(profileName)) {
    return null;
  }

  const tokens = text.match(/[가-힣]{2,8}/g) ?? [];
  const match = tokens
    .map((token) => stripParticle(token))
    .find((token) => isLikelyProfileNameMisrecognition(token, profileName));

  if (!match) {
    return null;
  }

  return {
    from: match,
    to: profileName,
    suggestedText: text.replace(match, profileName),
  };
}

function stripParticle(token: string) {
  return token.replace(/(이가|은|는|을|를|와|과|도|만|께|에게|한테|가)$/u, "");
}

function isLikelyProfileNameMisrecognition(token: string, profileName: string) {
  if (!token || token === profileName || Math.abs(token.length - profileName.length) > 1) {
    return false;
  }

  const tokenPhonemes = decomposeHangul(token);
  const profilePhonemes = decomposeHangul(profileName);
  const distance = levenshteinDistance(tokenPhonemes, profilePhonemes);
  const threshold = profileName.length <= 2 ? 3 : Math.ceil(profilePhonemes.length * 0.45);

  return distance > 0 && distance <= threshold;
}

function decomposeHangul(text: string) {
  return [...text].flatMap((char) => {
    const code = char.charCodeAt(0);
    if (code < hangulBase || code > hangulLast) {
      return [char];
    }

    const offset = code - hangulBase;
    const choseongIndex = Math.floor(offset / 588);
    const jungseongIndex = Math.floor((offset % 588) / 28);
    const jongseongIndex = offset % 28;
    return [choseong[choseongIndex], jungseong[jungseongIndex], jongseong[jongseongIndex]].filter(Boolean);
  });
}

function levenshteinDistance(left: string[], right: string[]) {
  const distances = Array.from({ length: left.length + 1 }, () => Array(right.length + 1).fill(0));
  for (let row = 0; row <= left.length; row += 1) {
    distances[row][0] = row;
  }
  for (let column = 0; column <= right.length; column += 1) {
    distances[0][column] = column;
  }

  for (let row = 1; row <= left.length; row += 1) {
    for (let column = 1; column <= right.length; column += 1) {
      const substitutionCost = left[row - 1] === right[column - 1] ? 0 : 1;
      distances[row][column] = Math.min(
        distances[row - 1][column] + 1,
        distances[row][column - 1] + 1,
        distances[row - 1][column - 1] + substitutionCost,
      );
    }
  }

  return distances[left.length][right.length];
}

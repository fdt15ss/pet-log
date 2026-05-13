import type { ContextCorrectionSuggestion } from "./voice-transcript-review";

export function mergeContextCorrectionSuggestions(
  ruleSuggestions: ContextCorrectionSuggestion[],
  llmSuggestions: ContextCorrectionSuggestion[],
) {
  const merged: ContextCorrectionSuggestion[] = [];
  const seen = new Set<string>();

  for (const suggestion of [...llmSuggestions, ...ruleSuggestions]) {
    const key = `${suggestion.from}\n${suggestion.to}\n${suggestion.suggestedText}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    merged.push(suggestion);
  }

  return merged;
}

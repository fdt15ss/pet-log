import type { StructuredRecord, StructuredRecordCandidate } from "./types";

type PreviewPayload = {
  structured: StructuredRecord;
  candidates: StructuredRecordCandidate[];
};

type ResolveRecordPreviewStateInput = {
  trimmedDetail: string;
  activePreview: PreviewPayload | null;
  savedPreview: PreviewPayload | null;
  fallbackPreview: StructuredRecord;
};

export function resolveRecordPreviewState({
  trimmedDetail,
  activePreview,
  savedPreview,
  fallbackPreview,
}: ResolveRecordPreviewStateInput) {
  const savedPreviewForEmptyInput = trimmedDetail ? null : savedPreview;
  const selectedPreview = activePreview ?? savedPreviewForEmptyInput;

  return {
    displayPreview: selectedPreview?.structured ?? fallbackPreview,
    activePreview: activePreview?.structured ?? null,
    activeCandidates: activePreview?.candidates ?? [],
    isShowingSavedPreview: !!savedPreviewForEmptyInput && !activePreview,
  };
}

import type { RecordCategory, RecordCategoryChoice, StructuredRecord } from "./types";

export type RecordInputMode = "text" | "voice" | "photo";

export type RecordInputModeStatus = "available" | "coming-soon";

export type RecordInputModeFeedback = {
  status: RecordInputModeStatus;
  label: string;
  detail: string;
};

export type BrowserSpeechRecognitionResult = {
  isFinal: boolean;
  0?: {
    transcript: string;
  };
};

export type BrowserSpeechRecognitionResultEvent = {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: BrowserSpeechRecognitionResult;
  };
};

export type BrowserSpeechRecognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  onresult: ((event: BrowserSpeechRecognitionResultEvent) => void) | null;
  start: () => void;
  stop: () => void;
};

export type BrowserSpeechRecognitionConstructor = new () => BrowserSpeechRecognition;

export type BrowserSpeechRecognitionWindow = {
  SpeechRecognition?: BrowserSpeechRecognitionConstructor;
  webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
};

export const recordInputFlow = ["category", "mode", "entry", "ai-preview", "recent-records"] as const;

export const defaultRecordCategoryChoice: RecordCategoryChoice = "all";

export const recordCategoryChoiceOptions = [
  { icon: "record", label: "AI 자동", value: "all", hint: "내용 기준" },
  { icon: "meal", label: "식사", value: "meal", hint: "먹은 양" },
  { icon: "walk", label: "산책", value: "walk", hint: "시간/거리" },
  { icon: "stool", label: "배변", value: "stool", hint: "횟수/상태" },
  { icon: "medical", label: "병원/약", value: "medical", hint: "약/진료" },
  { icon: "behavior", label: "행동", value: "behavior", hint: "감정/반응" },
] as const satisfies ReadonlyArray<{
  icon: "record" | RecordCategory;
  label: string;
  value: RecordCategoryChoice;
  hint: string;
}>;

export function resolveRecordCategoryForSave(choice: RecordCategoryChoice, structured: StructuredRecord): RecordCategory {
  return choice === "all" ? structured.suggestedCategory : choice;
}

export function getRecordCategoryChoiceLabel(choice: RecordCategoryChoice): string {
  return recordCategoryChoiceOptions.find((option) => option.value === choice)?.label ?? "";
}

const inputModeFeedback: Record<RecordInputMode, RecordInputModeFeedback> = {
  text: {
    status: "available",
    label: "바로 입력",
    detail: "자연어로 식사, 산책, 배변, 행동을 한 번에 적으면 AI가 구조화합니다.",
  },
  voice: {
    status: "available",
    label: "녹음",
    detail: "마이크로 녹음한 뒤 종료하면 자동으로 텍스트 변환해 기록 입력창에 채웁니다.",
  },
  photo: {
    status: "coming-soon",
    label: "준비 중",
    detail: "사진 첨부와 인식은 준비 중입니다. 사진과 함께 남길 메모를 먼저 입력할 수 있습니다.",
  },
};

export function getInputModeFeedback(mode: RecordInputMode) {
  return inputModeFeedback[mode];
}

export function getBrowserSpeechRecognitionConstructor(
  windowLike: BrowserSpeechRecognitionWindow = globalThis as BrowserSpeechRecognitionWindow,
) {
  return windowLike.SpeechRecognition ?? windowLike.webkitSpeechRecognition ?? null;
}

export function resolveSpeechRecognitionDetail({
  currentDetail,
  transcript,
  isFreshSession,
}: {
  currentDetail: string;
  transcript: string;
  isFreshSession: boolean;
}) {
  const trimmedTranscript = transcript.trim();
  if (isFreshSession) {
    return trimmedTranscript;
  }

  const trimmedCurrent = currentDetail.trim();
  return trimmedCurrent ? `${trimmedCurrent} ${trimmedTranscript}` : trimmedTranscript;
}

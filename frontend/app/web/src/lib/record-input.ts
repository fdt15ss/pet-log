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

export type RecordInputMode = "text" | "voice" | "photo";

export type RecordInputModeStatus = "available" | "coming-soon";

export type RecordInputModeFeedback = {
  status: RecordInputModeStatus;
  label: string;
  detail: string;
};

export const recordInputFlow = ["category", "mode", "entry", "ai-preview", "recent-records"] as const;

const inputModeFeedback: Record<RecordInputMode, RecordInputModeFeedback> = {
  text: {
    status: "available",
    label: "바로 입력",
    detail: "자연어로 식사, 산책, 배변, 행동을 한 번에 적으면 AI가 구조화합니다.",
  },
  voice: {
    status: "coming-soon",
    label: "준비 중",
    detail: "음성 녹음은 준비 중입니다. 지금은 말하듯 적은 메모를 저장해주세요.",
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

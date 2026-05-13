"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PetIcon } from "@/components/pet-icons";
import { usePetLog } from "@/components/pet-log-provider";
import {
  Card,
  CategoryBadge,
  SectionHeader,
  categoryBadgeColors,
} from "@/components/ui";
import {
  structureRecordPreview,
  suggestVoiceTranscriptCorrections,
  transcribeSpeechAudio,
} from "@/lib/api-client";
import { categoryLabels } from "@/lib/record-constants";
import {
  defaultRecordCategoryChoice,
  getBrowserSpeechRecognitionConstructor,
  getInputModeFeedback,
  getRecordCategoryChoiceLabel,
  recordCategoryChoiceOptions,
  resolveSpeechRecognitionDetail,
  resolveRecordCategoryForSave,
  type BrowserSpeechRecognition,
  type BrowserSpeechRecognitionConstructor,
  type BrowserSpeechRecognitionResultEvent,
  type RecordInputMode,
} from "@/lib/record-input";
import { resolveRecordPreviewState } from "@/lib/record-preview-state";
import { groupRecentRecordCards } from "@/lib/recent-record-groups";
import { mergeContextCorrectionSuggestions } from "@/lib/voice-transcript-corrections";
import type {
  ExtractedMeasurement,
  RecordCategory,
  RecordCategoryChoice,
  StructuredRecord,
  StructuredRecordCandidate,
} from "@/lib/types";
import {
  createVoiceTranscriptReview,
  type VoiceTranscriptReview,
} from "@/lib/voice-transcript-review";

const inputModes: { label: string; value: RecordInputMode }[] = [
  { label: "텍스트", value: "text" },
  { label: "음성", value: "voice" },
  { label: "사진", value: "photo" },
];

const inputPlaceholders: Record<RecordInputMode, string> = {
  text: "예: 오늘 아침에 50g 사료 먹고, 간식 조금 줬어. 낮에 산책 20분 했고 밤에 배변 1번 했어.",
  voice: "음성으로 남길 내용을 확인하거나 직접 수정해주세요.",
  photo: "사진과 함께 남길 메모를 입력해주세요.",
};

const maxLength = 500;

type AiPreviewResult = {
  detail: string;
  category: RecordCategoryChoice;
  structured: StructuredRecord;
  candidates: StructuredRecordCandidate[];
};

type VoiceReviewState = VoiceTranscriptReview & {
  confirmed: boolean;
};

function createPendingPreview(
  detail: string,
  category: RecordCategoryChoice,
): StructuredRecord {
  const sourceText = detail.trim();
  const firstSentence = sourceText.split(/\n|[.!?。]/)[0]?.trim() ?? sourceText;
  const suggestedCategory = category === "all" ? "meal" : category;

  return {
    sourceText,
    normalizedSummary: firstSentence
      ? firstSentence.length > 38
        ? `${firstSentence.slice(0, 38)}...`
        : firstSentence
      : "기록 내용을 입력하면 미리보기가 생성됩니다.",
    suggestedCategory,
    detectedCategories: [suggestedCategory],
    confidence: 0.4,
    measurements: [],
    needsConfirmation: true,
  };
}

const measurementKeywordsByCategory: Record<RecordCategory, string[]> = {
  meal: ["급여", "섭취", "사료", "밥", "간식", "비율"],
  walk: ["산책", "시간", "소요", "거리"],
  stool: ["소변", "대변", "배변", "변", "횟수"],
  medical: ["내용", "증상", "진료", "병원", "약", "부위", "상처", "피"],
  behavior: ["반응", "행동", "무서워", "짖", "불안", "흥분"],
};

function filterMeasurementsForCategory(
  measurements: ExtractedMeasurement[],
  category: RecordCategory,
): ExtractedMeasurement[] {
  const keywords = measurementKeywordsByCategory[category];

  return measurements.filter((measurement) => {
    const label = measurement.label ?? "";
    const value = measurement.value ?? "";
    const measurementText = `${label} ${value}`;

    const labelMatched = keywords.some((keyword) => label.includes(keyword));

    if (category === "meal") {
      const hasMealLabel = /급여|섭취|사료|밥|간식|비율|양|식사/.test(label);
      const hasMealValue = /사료|밥|간식|먹|급여|g|kg|그램|킬로|%/.test(value);

      return hasMealLabel || hasMealValue;
    }

    if (category === "walk") {
      const hasWalkLabel = /산책|걷|운동|소요|거리|시간/.test(label);
      const hasWalkValue = /산책|시간|분|km|m/.test(value);
      const hasWrongValue = /식사|사료|급여|소변|대변|병원|진료|무서워|짖/.test(
        value,
      );

      return hasWalkLabel && hasWalkValue && !hasWrongValue;
    }

    if (category === "stool") {
      return labelMatched || /소변|대변|배변|오줌|응가/.test(measurementText);
    }

    if (category === "medical") {
      return (
        labelMatched ||
        /병원|진료|피|상처|긁|약|구토|설사/.test(measurementText)
      );
    }

    if (category === "behavior") {
      return (
        labelMatched || /무서워|짖|불안|흥분|낑낑|떨/.test(measurementText)
      );
    }

    return labelMatched;
  });
}

function inferMeasurementsForDisplay(
  text: string,
  category: RecordCategory,
): ExtractedMeasurement[] {
  const normalizedText = text.replace(/\s+/g, " ").trim();

  if (!normalizedText) {
    return [];
  }

  if (category === "meal") {
    const amount =
      normalizedText.match(
        /(?:사료|밥|간식|급여).{0,16}?(\d+(?:\.\d+)?\s*(?:g|kg|그램|킬로))/u,
      )?.[1] ??
      normalizedText.match(
        /(\d+(?:\.\d+)?\s*(?:g|kg|그램|킬로)).{0,16}?(?:사료|밥|간식|먹|급여)/u,
      )?.[1];

    return amount
      ? [{ label: "식사", value: `사료 ${amount.replace(/\s+/g, "")}` }]
      : [];
  }

  if (category === "walk") {
    const duration =
      normalizedText.match(
        /산책.{0,24}?(\d+(?:\.\d+)?\s*(?:시간|분)|한\s*시간|반\s*시간)/u,
      )?.[1] ??
      normalizedText.match(
        /(\d+(?:\.\d+)?\s*(?:시간|분)|한\s*시간|반\s*시간).{0,24}?산책/u,
      )?.[1];

    if (!duration) {
      return [];
    }

    const formattedDuration = duration
      .replace(/(\d+(?:\.\d+)?)\s+(시간|분)/u, "$1$2")
      .replace(/한\s*시간/u, "한 시간")
      .replace(/반\s*시간/u, "반 시간")
      .trim();

    const walkTimeMatch = normalizedText.match(
      /(?:오늘\s*)?(아침|오전|점심|오후|저녁|밤)?\s*(\d{1,2})\s*시\s*(반)?(?:에)?\s*산책/u,
    );

    const hasToday = /오늘/.test(normalizedText);
    const hasMorning = /오늘\s*아침|아침/.test(normalizedText);
    const period = walkTimeMatch?.[1] ?? (hasMorning ? "아침" : "");
    const hour = walkTimeMatch?.[2];
    const half = walkTimeMatch?.[3];

    const timeText = hour
      ? `${hasToday ? "오늘 " : ""}${period ? `${period} ` : ""}${hour}시${half ? " 반" : ""}`
      : "";

    return [
      {
        label: "산책",
        value: `${timeText ? `${timeText}에 ` : ""}${formattedDuration} 산책`,
      },
    ];
  }

  if (category === "stool") {
    const types: string[] = [];

    if (/소변|오줌/.test(normalizedText)) {
      types.push("소변");
    }

    if (/대변|응가/.test(normalizedText)) {
      types.push("대변");
    }

    if (types.length === 0 && /배변|변/.test(normalizedText)) {
      types.push("배변");
    }

    return types.length > 0
      ? [{ label: "배변", value: types.join("과 ") }]
      : [];
  }

  if (category === "medical") {
    const medicalDetail =
      normalizedText.match(
        /(?:머리|귀|눈|코|입|피부|배|등|다리|발|손발).{0,50}?(?:긁|피|상처|아프|다치).{0,60}?(?:병원|진료|검진|처방).{0,40}?(?:받았어|받았|받음|갔|방문|다녀왔)/u,
      )?.[0] ??
      normalizedText.match(
        /(?:머리|귀|눈|코|입|피부|배|등|다리|발|손발).{0,80}?(?:병원|진료|검진|처방).{0,40}?(?:받았어|받았|받음|갔|방문|다녀왔)/u,
      )?.[0];

    return medicalDetail
      ? [{ label: "병원/접종", value: medicalDetail.trim() }]
      : [];
  }

  if (category === "behavior") {
    const behaviorDetail =
      normalizedText.match(
        /(?:진료를 받는데|진료를 받았는데|진료 중|병원에서).{0,60}?(?:무서워|짖|불안|흥분|떨|낑낑).*/u,
      )?.[0] ??
      normalizedText.match(/(?:무서워|짖|불안|흥분|떨|낑낑).{0,60}/u)?.[0];

    return behaviorDetail
      ? [{ label: "행동", value: behaviorDetail.trim() }]
      : [];
  }

  return [];
}

function normalizeKoreanDurationText(text: string) {
  const hourMap: Record<string, string> = {
    한: "1",
    두: "2",
    세: "3",
    네: "4",
    다섯: "5",
    여섯: "6",
    일곱: "7",
    여덟: "8",
    아홉: "9",
    열: "10",
  };

  return text.replace(
    /(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열)\s*시간/g,
    (_, koreanNumber: string) => `${hourMap[koreanNumber]}시간`,
  );
}

function uniqueCategories(categories: RecordCategory[]) {
  return categories.filter(
    (category, index) => categories.indexOf(category) === index,
  );
}

function isOtherCategoryLabel(text: string, category: RecordCategory) {
  const normalizedText = text.trim();

  return Object.entries(categoryLabels).some(
    ([candidateCategory, label]) =>
      candidateCategory !== category && normalizedText === label,
  );
}

type RecentDisplayRecord = {
  title: string;
  detail: string;
  category: RecordCategory;
  structured?: {
    sourceText?: string;
  };
};

function normalizeRecentRecordTitle(record: RecentDisplayRecord) {
  return categoryLabels[record.category] || record.title.trim() || "기록";
}

function normalizeRecentRecordDetail(record: RecentDisplayRecord) {
  const detail = record.detail.replace(/\s+/g, " ").trim();
  const sourceText = (record.structured?.sourceText || detail)
    .replace(/\s+/g, " ")
    .trim();

  const displayMeasurements = inferMeasurementsForDisplay(
    sourceText || detail,
    record.category,
  );

  const firstDisplayMeasurement = displayMeasurements[0];

  if (firstDisplayMeasurement) {
    return firstDisplayMeasurement.value;
  }

  if (record.category === "meal") {
    const mealAmount = detail.match(
      /(\d+(?:\.\d+)?\s*(?:g|kg|그램|킬로))/u,
    )?.[1];

    if (mealAmount) {
      return `사료 ${mealAmount.replace(/\s+/g, "")}`;
    }

    return detail
      .replace(/^사료\s*사료/u, "사료 ")
      .replace(/\s+/g, " ")
      .trim();
  }

  if (record.category === "behavior") {
    const behaviorDetail =
      sourceText.match(
        /(?:진료를 받는데|진료를 받았는데|진료 중|병원에서).{0,80}?(?:무서워|짖|불안|흥분|떨|낑낑).*/u,
      )?.[0] ??
      sourceText.match(/(?:무서워|짖|불안|흥분|떨|낑낑).{0,80}/u)?.[0] ??
      detail.match(
        /(?:진료를 받는데|진료를 받았는데|진료 중|병원에서).{0,80}?(?:무서워|짖|불안|흥분|떨|낑낑).*/u,
      )?.[0] ??
      detail.match(/(?:무서워|짖|불안|흥분|떨|낑낑).{0,80}/u)?.[0];

    return behaviorDetail?.trim() || detail;
  }

  return detail;
}

export default function RecordPage() {
  const { addRecord, profile, records } = usePetLog();

  const [detail, setDetail] = useState("");
  const [previewTab, setPreviewTab] = useState<RecordCategory | null>(null);
  const [category, setCategory] = useState<RecordCategoryChoice>(
    defaultRecordCategoryChoice,
  );
  const [inputMode, setInputMode] = useState<RecordInputMode>("voice");
  const [error, setError] = useState("");
  const [savedId, setSavedId] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [aiPreview, setAiPreview] = useState<AiPreviewResult | null>(null);
  const [lastSavedPreview, setLastSavedPreview] =
    useState<AiPreviewResult | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isCorrectionLoading, setIsCorrectionLoading] = useState(false);
  const [voiceReview, setVoiceReview] = useState<VoiceReviewState | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const speechRecognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const correctionRequestIdRef = useRef(0);
  const correctionDebounceTimerRef = useRef<number | null>(null);
  const pendingCorrectionTextRef = useRef("");
  const completedCorrectionTextRef = useRef("");
  const isFreshSpeechRecognitionSessionRef = useRef(false);

  useEffect(() => {
    console.log(
      "[record/page] records 업데이트:",
      records.length,
      "건",
      records.slice(0, 3).map((record) => record.id),
    );
  }, [records]);

  const recentRecordGroups = useMemo(
    () => groupRecentRecordCards(records, 3),
    [records],
  );
  const trimmedDetail = detail.trim();
  const hasActivePet = !!profile.id;
  const isInvalid =
    trimmedDetail.length < 5 || trimmedDetail.length > maxLength;
  const needsVoiceConfirmation =
    inputMode === "voice" && !!voiceReview && !voiceReview.confirmed;
  const fallbackPreview = useMemo(
    () => createPendingPreview(trimmedDetail, category),
    [category, trimmedDetail],
  );

  const activeAiPreview =
    !needsVoiceConfirmation &&
    aiPreview?.detail === trimmedDetail &&
    aiPreview.category === category
      ? { structured: aiPreview.structured, candidates: aiPreview.candidates }
      : null;

  const savedAiPreview = lastSavedPreview
    ? {
        structured: lastSavedPreview.structured,
        candidates: lastSavedPreview.candidates,
      }
    : null;

  const {
    displayPreview,
    activePreview,
    activeCandidates,
    isShowingSavedPreview,
  } = resolveRecordPreviewState({
    trimmedDetail,
    activePreview: activeAiPreview,
    savedPreview: savedAiPreview,
    fallbackPreview,
  });

  const resolvedCategory = resolveRecordCategoryForSave(
    category,
    displayPreview,
  );
  const showPreviewLoading =
    !!trimmedDetail &&
    isPreviewLoading &&
    !activePreview &&
    !needsVoiceConfirmation;
  const visiblePreviewError = needsVoiceConfirmation
    ? "음성 인식 결과를 먼저 확인해주세요."
    : trimmedDetail
      ? previewError
      : "";
  const confidencePercent = Math.round(displayPreview.confidence * 100);
  const savedPreviewMessage =
    "방금 저장한 AI 구조화 결과입니다. 새 기록을 입력하면 미리보기가 다시 생성됩니다.";
  const modeFeedback = getInputModeFeedback(inputMode);

  const detectedCategories = useMemo(() => {
    const categories = activeCandidates.length
      ? activeCandidates.map((candidate) => candidate.category)
      : displayPreview.detectedCategories?.length
        ? displayPreview.detectedCategories
        : [displayPreview.suggestedCategory];

    return uniqueCategories(categories);
  }, [
    activeCandidates,
    displayPreview.detectedCategories,
    displayPreview.suggestedCategory,
  ]);

  const activeDisplayCategory =
    previewTab && detectedCategories.includes(previewTab)
      ? previewTab
      : displayPreview.suggestedCategory;

  const selectedCandidate = useMemo(
    () =>
      activeCandidates.find(
        (candidate) => candidate.category === activeDisplayCategory,
      ) ?? null,
    [activeCandidates, activeDisplayCategory],
  );

  const previewTitle = useMemo(() => {
    if (!trimmedDetail) {
      return "기록 내용을 입력하면 미리보기가 생성됩니다.";
    }

    return trimmedDetail.length > 28
      ? `${trimmedDetail.slice(0, 28)}...`
      : trimmedDetail;
  }, [trimmedDetail]);

  const previewSourceTextForDisplay =
    trimmedDetail ||
    lastSavedPreview?.detail ||
    aiPreview?.detail ||
    displayPreview.sourceText ||
    selectedCandidate?.detail ||
    previewTitle;

  const inferredDisplayMeasurements = useMemo(
    () =>
      inferMeasurementsForDisplay(
        previewSourceTextForDisplay,
        activeDisplayCategory,
      ),
    [activeDisplayCategory, previewSourceTextForDisplay],
  );

  const candidateDetailForDisplay = selectedCandidate?.detail?.trim() ?? "";
  const normalizedSummaryForDisplay = displayPreview.normalizedSummary.trim();

  const activeDisplaySummary =
    inferredDisplayMeasurements[0]?.value ||
    (candidateDetailForDisplay &&
    !isOtherCategoryLabel(candidateDetailForDisplay, activeDisplayCategory)
      ? candidateDetailForDisplay
      : "") ||
    (normalizedSummaryForDisplay &&
    !isOtherCategoryLabel(normalizedSummaryForDisplay, activeDisplayCategory)
      ? normalizedSummaryForDisplay
      : "") ||
    previewTitle;

  const activeDisplayMeasurements = useMemo(() => {
    if (inferredDisplayMeasurements.length > 0) {
      return inferredDisplayMeasurements;
    }

    const baseMeasurements = selectedCandidate
      ? selectedCandidate.measurements
      : displayPreview.measurements;

    const filteredMeasurements = filterMeasurementsForCategory(
      baseMeasurements,
      activeDisplayCategory,
    );

    return filteredMeasurements
      .filter(
        (measurement) =>
          !isOtherCategoryLabel(measurement.value ?? "", activeDisplayCategory),
      )
      .map((measurement) => ({
        ...measurement,
        label: categoryLabels[activeDisplayCategory],
      }));
  }, [
    activeDisplayCategory,
    displayPreview.measurements,
    inferredDisplayMeasurements,
    selectedCandidate,
  ]);

  const activeDisplayConfidence = selectedCandidate
    ? Math.round(selectedCandidate.confidence * 100)
    : confidencePercent;

  const activeDisplayNeedsConfirmation = selectedCandidate
    ? selectedCandidate.needsConfirmation
    : displayPreview.needsConfirmation;

  useEffect(() => {
    if (!trimmedDetail || !hasActivePet) {
      return;
    }

    if (needsVoiceConfirmation) {
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(() => {
      setIsPreviewLoading(true);
      structureRecordPreview({
        detail: trimmedDetail,
        fallbackCategory: category,
      })
        .then((response) => {
          if (!cancelled) {
            console.log(
              "[record/page] AI 미리보기 성공:",
              response.structured.suggestedCategory,
              `${Math.round(response.structured.confidence * 100)}%`,
            );
            setAiPreview({
              category,
              detail: trimmedDetail,
              structured: response.structured,
              candidates: response.candidates,
            });
            setPreviewError("");
          }
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            console.log(
              "[record/page] AI 미리보기 실패:",
              err instanceof Error ? err.message : err,
            );
            setAiPreview(null);
            setPreviewError(
              "AI 미리보기를 불러오지 못해 기본 분류로 표시합니다.",
            );
          }
        })
        .finally(() => {
          if (!cancelled) {
            setIsPreviewLoading(false);
          }
        });
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [category, hasActivePet, needsVoiceConfirmation, trimmedDetail]);

  useEffect(() => {
    return () => {
      clearCorrectionDebounceTimer();
      speechRecognitionRef.current?.stop();
      stopMediaStream();
    };
  }, []);

  function stopMediaStream() {
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
  }

  function resetVoiceRecordingDraft() {
    clearCorrectionDebounceTimer();
    correctionRequestIdRef.current += 1;
    pendingCorrectionTextRef.current = "";
    completedCorrectionTextRef.current = "";
    isFreshSpeechRecognitionSessionRef.current = true;
    setDetail("");
    setVoiceReview(null);
    setAiPreview(null);
    setLastSavedPreview(null);
    setPreviewError("");
    setError("");
    setSavedId(null);
    setSaveMessage("");
    setIsCorrectionLoading(false);
  }

  async function handleSave() {
    if (!hasActivePet) {
      setError("반려동물을 먼저 등록해주세요.");
      setSavedId(null);
      return;
    }

    if (!trimmedDetail) {
      setError("기록 내용을 입력해주세요.");
      setSavedId(null);
      setSaveMessage("");
      return;
    }

    if (needsVoiceConfirmation) {
      setError("음성 인식 결과를 먼저 확인해주세요.");
      setSavedId(null);
      setSaveMessage("");
      return;
    }

    if (trimmedDetail.length < 5) {
      setError("기록은 5자 이상 입력해주세요.");
      setSavedId(null);
      setSaveMessage("");
      return;
    }

    if (trimmedDetail.length > maxLength) {
      setError(`기록은 ${maxLength}자 이내로 입력해주세요.`);
      setSavedId(null);
      setSaveMessage("");
      return;
    }

    setIsSaving(true);

    try {
      let saveStructured = activePreview;
      let saveCandidates = activeCandidates;

      if (!activePreview) {
        try {
          const response = await structureRecordPreview({
            detail: trimmedDetail,
            fallbackCategory: category,
          });

          console.log(
            "[record/page] structureRecordPreview 성공:",
            response.structured.suggestedCategory,
          );

          setAiPreview({
            category,
            detail: trimmedDetail,
            structured: response.structured,
            candidates: response.candidates,
          });

          saveStructured = response.structured;
          saveCandidates = response.candidates;
          setPreviewError("");
        } catch (err) {
          console.log(
            "[record/page] structureRecordPreview 실패:",
            err instanceof Error ? err.message : err,
          );
          setPreviewError(
            "AI 미리보기를 불러오지 못했습니다. 저장 시 서버에서 다시 처리합니다.",
          );
        }
      }

      const fallbackStructured = createPendingPreview(trimmedDetail, category);
      const snapshotCategories = uniqueCategories(
        saveCandidates.length
          ? saveCandidates.map((candidate) => candidate.category)
          : saveStructured?.detectedCategories?.length
            ? saveStructured.detectedCategories
            : [resolvedCategory],
      );

      const savedPreviewSnapshot: AiPreviewResult = {
        category,
        detail: trimmedDetail,
        structured: {
          ...(saveStructured ?? fallbackStructured),
          sourceText: trimmedDetail,
          detectedCategories: snapshotCategories,
        },
        candidates: saveCandidates.map((candidate) => ({
          ...candidate,
          detail: candidate.detail || trimmedDetail,
          measurements:
            candidate.measurements.length > 0
              ? candidate.measurements
              : inferMeasurementsForDisplay(trimmedDetail, candidate.category),
        })),
      };

      console.log(
        "[record/page] addRecord 호출:",
        category,
        trimmedDetail.slice(0, 30),
      );

      const result = await addRecord({
        category,
        detail: trimmedDetail,
        structured: saveStructured ?? undefined,
        candidates: saveCandidates,
        source: inputMode === "voice" ? "voice" : "manual",
      });

      console.log("[record/page] addRecord 성공:", result.record.id);
      setSavedId(result.record.id);
      setSaveMessage(result.storageMessage);
      setError("");
      setLastSavedPreview(savedPreviewSnapshot);
      setDetail("");
      setVoiceReview(null);
    } catch (err) {
      console.log(
        "[record/page] addRecord 실패:",
        err instanceof Error ? err.message : err,
      );
      setSavedId(null);
      setSaveMessage("");
      setError("기록 저장에 실패했습니다. 서버 연결을 확인해주세요.");
    } finally {
      setIsSaving(false);
    }
  }

  async function transcribeRecordedAudio(audio: Blob) {
    if (!audio.size) {
      setError("녹음된 음성이 없습니다. 다시 녹음해주세요.");
      return;
    }

    setIsTranscribing(true);
    setError("");
    setSavedId(null);

    try {
      const fileType = audio.type || "audio/webm";
      const file = new File([audio], "recording.webm", { type: fileType });
      console.log(
        "[record/page] transcribeSpeechAudio 호출:",
        fileType,
        audio.size,
        "bytes",
      );
      const transcription = await transcribeSpeechAudio(file);
      console.log(
        "[record/page] transcribeSpeechAudio 성공:",
        transcription.text.slice(0, 50),
      );
      applyVoiceTranscript(transcription.text);
    } catch (err) {
      console.log(
        "[record/page] transcribeSpeechAudio 실패:",
        err instanceof Error ? err.message : err,
      );
      setError("음성 인식에 실패했습니다. 텍스트로 직접 입력해주세요.");
    } finally {
      setIsTranscribing(false);
    }
  }

  function normalizeCorrectionText(text: string) {
    return text.replace(/\s+/g, " ").trim();
  }

  function clearCorrectionDebounceTimer() {
    if (correctionDebounceTimerRef.current !== null) {
      window.clearTimeout(correctionDebounceTimerRef.current);
      correctionDebounceTimerRef.current = null;
    }
  }

  function scheduleVoiceCorrectionSuggestions(text: string) {
    const normalizedText = normalizeCorrectionText(text);

    if (!normalizedText) {
      return;
    }

    if (
      pendingCorrectionTextRef.current === normalizedText ||
      completedCorrectionTextRef.current === normalizedText
    ) {
      return;
    }

    clearCorrectionDebounceTimer();
    correctionDebounceTimerRef.current = window.setTimeout(() => {
      correctionDebounceTimerRef.current = null;
      void loadVoiceCorrectionSuggestions(normalizedText);
    }, 700);
  }

  function applySpeechRecognitionResult(
    event: BrowserSpeechRecognitionResultEvent,
  ) {
    const transcriptParts: string[] = [];
    for (
      let index = event.resultIndex;
      index < event.results.length;
      index += 1
    ) {
      const transcript = event.results[index]?.[0]?.transcript.trim();
      if (transcript) {
        transcriptParts.push(transcript);
      }
    }

    const transcript = transcriptParts.join(" ").trim();
    if (transcript) {
      const isFreshSession = isFreshSpeechRecognitionSessionRef.current;
      isFreshSpeechRecognitionSessionRef.current = false;
      setDetail((currentDetail) => {
        const nextDetail = normalizeKoreanDurationText(
          resolveSpeechRecognitionDetail({
            currentDetail,
            transcript,
            isFreshSession,
          }),
        );
        const review = createVoiceTranscriptReview(nextDetail, profile.name);
        setVoiceReview({ ...review, confirmed: false });
        scheduleVoiceCorrectionSuggestions(nextDetail);
        return nextDetail;
      });
    }
  }

  function applyVoiceTranscript(transcript: string) {
    const normalizedTranscript = normalizeKoreanDurationText(transcript);
    const review = createVoiceTranscriptReview(
      normalizedTranscript,
      profile.name,
    );

    setDetail(review.confirmedText);
    setVoiceReview({ ...review, confirmed: false });
    scheduleVoiceCorrectionSuggestions(review.confirmedText);
  }

  async function loadVoiceCorrectionSuggestions(text: string) {
    const trimmedText = normalizeCorrectionText(text);
    if (!trimmedText) {
      return;
    }

    if (
      pendingCorrectionTextRef.current === trimmedText ||
      completedCorrectionTextRef.current === trimmedText
    ) {
      return;
    }

    const requestId = correctionRequestIdRef.current + 1;
    correctionRequestIdRef.current = requestId;
    pendingCorrectionTextRef.current = trimmedText;
    setIsCorrectionLoading(true);

    try {
      const response = await suggestVoiceTranscriptCorrections({
        text: trimmedText,
        profileName: profile.name,
      });
      setVoiceReview((currentReview) => {
        if (!currentReview || correctionRequestIdRef.current !== requestId) {
          return currentReview;
        }
        const ruleReview = createVoiceTranscriptReview(
          currentReview.confirmedText || trimmedText,
          profile.name,
        );
        return {
          ...currentReview,
          contextCorrectionSuggestions: mergeContextCorrectionSuggestions(
            ruleReview.contextCorrectionSuggestions,
            response.suggestions,
          ),
        };
      });

      if (correctionRequestIdRef.current === requestId) {
        completedCorrectionTextRef.current = trimmedText;
      }
    } catch {
      // 기존 규칙 기반 제안은 이미 화면에 표시되어 있으므로 LLM 실패는 조용히 무시합니다.
    } finally {
      if (pendingCorrectionTextRef.current === trimmedText) {
        pendingCorrectionTextRef.current = "";
      }

      if (correctionRequestIdRef.current === requestId) {
        setIsCorrectionLoading(false);
      }
    }
  }

  function handleApplyProfileNameSuggestion() {
    const suggestion = voiceReview?.profileNameSuggestion;
    if (!suggestion) {
      return;
    }

    const nextReview = createVoiceTranscriptReview(
      suggestion.suggestedText,
      profile.name,
    );
    setDetail(suggestion.suggestedText);
    setVoiceReview({
      ...nextReview,
      recognizedText: suggestion.suggestedText,
      confirmedText: suggestion.suggestedText,
      confirmed: false,
    });
  }

  function handleKeepRecognizedPetName() {
    if (!voiceReview) {
      return;
    }

    setVoiceReview({ ...voiceReview, profileNameSuggestion: null });
  }

  function applySingleContextCorrectionToText(
    text: string,
    suggestion: VoiceReviewState["contextCorrectionSuggestions"][number],
  ) {
    if (!suggestion.from || !suggestion.to) {
      return text;
    }

    if (!text.includes(suggestion.from)) {
      return text;
    }

    return text.replace(suggestion.from, suggestion.to);
  }

  function handleApplyContextCorrection(index: number) {
    const suggestion = voiceReview?.contextCorrectionSuggestions[index];
    if (!voiceReview || !suggestion) {
      return;
    }

    const baseText =
      trimmedDetail || voiceReview.confirmedText || voiceReview.recognizedText;

    const correctedText = normalizeKoreanDurationText(
      applySingleContextCorrectionToText(baseText, suggestion),
    );

    const nextReview = createVoiceTranscriptReview(correctedText, profile.name);

    const remainingSuggestions = voiceReview.contextCorrectionSuggestions
      .filter((_, suggestionIndex) => suggestionIndex !== index)
      .map((remainingSuggestion) => ({
        ...remainingSuggestion,
        suggestedText: applySingleContextCorrectionToText(
          correctedText,
          remainingSuggestion,
        ),
      }));

    setDetail(correctedText);
    setVoiceReview({
      ...nextReview,
      recognizedText: correctedText,
      confirmedText: correctedText,
      confirmed: false,
      profileNameSuggestion: null,
      contextCorrectionSuggestions: mergeContextCorrectionSuggestions(
        nextReview.contextCorrectionSuggestions,
        remainingSuggestions,
      ),
    });
  }

  function handleKeepContextCorrection(index: number) {
    if (!voiceReview) {
      return;
    }

    setVoiceReview({
      ...voiceReview,
      contextCorrectionSuggestions:
        voiceReview.contextCorrectionSuggestions.filter(
          (_, suggestionIndex) => suggestionIndex !== index,
        ),
    });
  }

  function handleConfirmVoiceReview() {
    if (!voiceReview) {
      return;
    }

    const confirmedText = normalizeKoreanDurationText(
      trimmedDetail || voiceReview.confirmedText || voiceReview.recognizedText,
    );

    setDetail(confirmedText);
    setVoiceReview({
      ...voiceReview,
      recognizedText: confirmedText,
      confirmedText,
      confirmed: true,
      profileNameSuggestion: null,
      contextCorrectionSuggestions: [],
    });
    setAiPreview(null);
    setLastSavedPreview(null);
    setPreviewError("");
    setIsCorrectionLoading(false);
    setError("");
  }

  function startBrowserSpeechRecognition(
    SpeechRecognition: BrowserSpeechRecognitionConstructor,
  ) {
    const recognition = new SpeechRecognition();
    recognition.lang = "ko-KR";
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.onresult = applySpeechRecognitionResult;
    recognition.onerror = () => {
      speechRecognitionRef.current = null;
      setIsRecording(false);
      setError(
        "브라우저 음성 인식에 실패했습니다. 다시 녹음하거나 텍스트로 입력해주세요.",
      );
    };
    recognition.onend = () => {
      speechRecognitionRef.current = null;
      setIsRecording(false);
    };

    speechRecognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
  }

  async function startServerRecordingFallback() {
    if (
      !navigator.mediaDevices?.getUserMedia ||
      typeof MediaRecorder === "undefined"
    ) {
      setError("이 브라우저에서는 음성 녹음을 사용할 수 없습니다.");
      return;
    }

    setError("");
    setSavedId(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current = [...audioChunksRef.current, event.data];
        }
      };
      recorder.onstop = () => {
        const audio = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        mediaRecorderRef.current = null;
        audioChunksRef.current = [];
        stopMediaStream();
        void transcribeRecordedAudio(audio);
      };

      recorder.start();
      setIsRecording(true);
    } catch {
      stopMediaStream();
      mediaRecorderRef.current = null;
      setError("마이크 권한을 확인한 뒤 다시 녹음해주세요.");
    }
  }

  async function startRecording() {
    resetVoiceRecordingDraft();
    const SpeechRecognition = getBrowserSpeechRecognitionConstructor();

    if (SpeechRecognition) {
      try {
        startBrowserSpeechRecognition(SpeechRecognition);
        return;
      } catch {
        speechRecognitionRef.current = null;
        setIsRecording(false);
      }
    }

    await startServerRecordingFallback();
  }

  function stopRecording() {
    const recognition = speechRecognitionRef.current;
    if (recognition) {
      speechRecognitionRef.current = null;
      setIsRecording(false);
      recognition.stop();
      return;
    }

    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      setIsRecording(false);
      stopMediaStream();
      return;
    }

    setIsRecording(false);
    recorder.stop();
  }

  function handleRecordingButtonClick() {
    if (isRecording) {
      stopRecording();
      return;
    }

    void startRecording();
  }

  return (
    <AppShell
      bottomAction={
        <button
          className={`pet-log-pressable h-12 w-full rounded-2xl text-base font-bold text-white shadow-[0_8px_22px_rgba(22,128,75,0.25)] disabled:bg-[#8ab99f] ${
            isInvalid || needsVoiceConfirmation || !hasActivePet
              ? "bg-[#8ab99f]"
              : "bg-[#16804b]"
          }`}
          disabled={
            isSaving || isInvalid || needsVoiceConfirmation || !hasActivePet
          }
          onClick={handleSave}
          type="button"
        >
          {isSaving ? "저장 중" : "기록 저장하기"}
        </button>
      }
      subtitle="자연어로 쉽고 빠르게 기록"
      title="기록 입력"
    >
      <div className="space-y-5">
        <Card
          className="bg-gradient-to-br from-white to-[#edf8ed]"
          motion="rise"
        >
          <p className="inline-flex items-center gap-1.5 text-sm font-bold text-[#16804b]">
            <PetIcon className="h-4 w-4" name="sparkle" />
            기록 준비
          </p>
          <h2 className="mt-1 text-lg font-black text-[#1f2922]">
            오늘 케어 내용을 한 번에 정리해요
          </h2>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <p className="text-[11px] font-bold text-[#778174]">분류</p>
              <p className="mt-1 truncate text-sm font-black text-[#1f2922]">
                {getRecordCategoryChoiceLabel(category)}
              </p>
            </div>
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <p className="text-[11px] font-bold text-[#778174]">AI 신뢰도</p>
              <p className="mt-1 text-sm font-black text-[#1f2922]">
                {confidencePercent}%
              </p>
            </div>
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <p className="text-[11px] font-bold text-[#778174]">입력</p>
              <p className="mt-1 text-sm font-black text-[#1f2922]">
                {detail.length}/{maxLength}
              </p>
            </div>
          </div>
        </Card>

        <section>
          <SectionHeader title="빠른 입력" />
          <div className="grid grid-cols-2 gap-2">
            {recordCategoryChoiceOptions.map((item) => {
              const active = item.value === category;
              return (
                <button
                  aria-pressed={active}
                  className={`pet-log-pressable flex min-h-16 items-center gap-3 rounded-2xl border px-3 text-left text-sm font-bold transition ${
                    active
                      ? "border-[#16804b] bg-[#16804b] text-white"
                      : "border-[#dfe6d9] bg-white text-[#4a5547] shadow-[0_8px_22px_rgba(49,65,44,0.05)]"
                  }`}
                  key={item.label}
                  onClick={() => setCategory(item.value)}
                  type="button"
                >
                  <span
                    className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${
                      active ? "bg-white/20" : "bg-[#f4f7f0] text-[#16804b]"
                    }`}
                  >
                    <PetIcon
                      className="h-5 w-5"
                      name={active ? "check" : item.icon}
                    />
                  </span>
                  <span className="min-w-0">
                    <span className="block">{item.label}</span>
                    <span
                      className={`mt-1 block text-[11px] font-semibold ${active ? "text-white/80" : "text-[#7c8777]"}`}
                    >
                      {item.hint}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        </section>

        <Card motion="rise">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-[#1f2922]">입력 방식</h2>
              <p className="mt-1 text-xs font-semibold text-[#7c8777]">
                현재 저장은 텍스트 메모 기준으로 동작합니다.
              </p>
            </div>
            {category === "all" ? (
              <span className="rounded-full bg-[#f1f5ed] px-2.5 py-1 text-xs font-bold text-[#53604f]">
                {getRecordCategoryChoiceLabel(category)}
              </span>
            ) : (
              <CategoryBadge category={resolvedCategory} />
            )}
          </div>
          <div className="grid grid-cols-3 gap-2">
            {inputModes.map((mode) => {
              const active = inputMode === mode.value;
              const feedback = getInputModeFeedback(mode.value);
              return (
                <button
                  aria-pressed={active}
                  className={`pet-log-pressable min-h-14 rounded-xl border px-2 text-sm font-bold ${
                    active
                      ? "border-[#16804b] bg-[#e7f4eb] text-[#0b7a43]"
                      : "border-[#dce5d5] bg-white text-[#40513f]"
                  }`}
                  key={mode.value}
                  onClick={() => setInputMode(mode.value)}
                  type="button"
                >
                  <span className="block">{mode.label}</span>
                  <span className="mt-1 block text-[11px] font-semibold opacity-80">
                    {feedback.label}
                  </span>
                </button>
              );
            })}
          </div>
          <div
            className={`mt-3 rounded-2xl px-4 py-3 ${
              modeFeedback.status === "available"
                ? "bg-[#edf8ed] text-[#356342]"
                : "bg-[#fff7ed] text-[#7a5531]"
            }`}
          >
            <p className="text-xs font-bold">{modeFeedback.label}</p>
            <p className="mt-1 text-xs leading-5">{modeFeedback.detail}</p>
          </div>

          {inputMode === "voice" ? (
            <button
              className={`pet-log-pressable mt-3 flex min-h-12 w-full items-center justify-center rounded-xl border px-4 text-sm font-bold ${
                isRecording
                  ? "border-[#be4c3c] bg-[#fff1ee] text-[#be4c3c]"
                  : "border-[#cfe2cd] bg-white text-[#16804b]"
              }`}
              disabled={isTranscribing}
              onClick={handleRecordingButtonClick}
              type="button"
            >
              {isTranscribing
                ? "음성 변환 중"
                : isRecording
                  ? "녹음 종료"
                  : "녹음 시작"}
            </button>
          ) : null}

          {inputMode === "voice" && voiceReview ? (
            <div
              className={`mt-3 rounded-2xl border px-4 py-3 ${
                voiceReview.confirmed
                  ? "border-[#cfe2cd] bg-[#f4faf2]"
                  : "border-[#f0d7a8] bg-[#fff8ec]"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-black text-[#1f2922]">
                    음성 인식 결과 확인
                  </p>
                  <p className="mt-1 text-xs leading-5 text-[#667262]">
                    저장 전에 인식된 문장을 확인하고, 필요하면 아래 기록 칸에서
                    직접 고쳐주세요.
                  </p>
                  {isCorrectionLoading ? (
                    <p className="mt-1 text-xs font-bold leading-5 text-[#9a6518]">
                      AI가 문맥 교정 제안을 확인 중입니다.
                    </p>
                  ) : null}
                </div>
                <span
                  className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-black ${
                    voiceReview.confirmed
                      ? "bg-[#e3f4de] text-[#32783c]"
                      : "bg-[#fff0cf] text-[#9a6518]"
                  }`}
                >
                  {voiceReview.confirmed ? "확인 완료" : "확인 필요"}
                </span>
              </div>

              <p className="mt-3 rounded-xl bg-white/75 px-3 py-2 text-xs font-semibold leading-5 text-[#4a5547]">
                {voiceReview.confirmedText ||
                  detail ||
                  voiceReview.recognizedText}
              </p>

              {voiceReview.profileNameSuggestion ? (
                <div className="mt-3 rounded-xl bg-white px-3 py-3">
                  <p className="text-xs font-bold leading-5 text-[#4a5547]">
                    <span className="font-black text-[#1f2922]">
                      {voiceReview.profileNameSuggestion.from}
                    </span>
                    를 프로필 이름{" "}
                    <span className="font-black text-[#1f2922]">
                      {voiceReview.profileNameSuggestion.to}
                    </span>
                    로 바꿀까요?
                  </p>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    <button
                      className="pet-log-pressable h-10 rounded-xl bg-[#16804b] text-xs font-black text-white"
                      onClick={handleApplyProfileNameSuggestion}
                      type="button"
                    >
                      프로필 이름 적용
                    </button>
                    <button
                      className="pet-log-pressable h-10 rounded-xl border border-[#dfe6d9] bg-white text-xs font-black text-[#53604f]"
                      onClick={handleKeepRecognizedPetName}
                      type="button"
                    >
                      그대로 두기
                    </button>
                  </div>
                </div>
              ) : null}

              {voiceReview.contextCorrectionSuggestions.map(
                (suggestion, index) => (
                  <div
                    className="mt-3 rounded-xl bg-white px-3 py-3"
                    key={`${suggestion.from}-${suggestion.to}-${index}`}
                  >
                    <p className="text-xs font-bold leading-5 text-[#4a5547]">
                      <span className="font-black text-[#1f2922]">
                        {suggestion.from}
                      </span>
                      는 문맥상{" "}
                      <span className="font-black text-[#1f2922]">
                        {suggestion.to}
                      </span>
                      일 수 있어요. 바꿀까요?
                    </p>
                    <p className="mt-1 text-[11px] font-semibold leading-5 text-[#7c8777]">
                      {suggestion.reason}
                    </p>
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      <button
                        className="pet-log-pressable h-10 rounded-xl bg-[#16804b] text-xs font-black text-white"
                        onClick={() => handleApplyContextCorrection(index)}
                        type="button"
                      >
                        {suggestion.to}로 바꾸기
                      </button>
                      <button
                        className="pet-log-pressable h-10 rounded-xl border border-[#dfe6d9] bg-white text-xs font-black text-[#53604f]"
                        onClick={() => handleKeepContextCorrection(index)}
                        type="button"
                      >
                        그대로 두기
                      </button>
                    </div>
                  </div>
                ),
              )}

              <button
                className="pet-log-pressable mt-3 h-10 w-full rounded-xl border border-[#cfe2cd] bg-white text-sm font-black text-[#16804b]"
                onClick={handleConfirmVoiceReview}
                type="button"
              >
                이 내용으로 분석하기
              </button>
            </div>
          ) : null}
        </Card>

        <Card motion="rise">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-bold">자연어 기록</h2>
            <span
              className={`text-xs font-semibold ${detail.length > maxLength ? "text-[#be4c3c]" : "text-[#9aa494]"}`}
            >
              {detail.length}/{maxLength}
            </span>
          </div>
          <textarea
            className="min-h-40 w-full resize-none rounded-2xl border border-[#dde6d6] bg-[#fbfcfa] p-4 text-sm leading-6 outline-none placeholder:text-[#8a9286] focus:border-[#16804b] focus:ring-2 focus:ring-[#16804b]/15"
            maxLength={maxLength + 40}
            onChange={(event) => {
              const nextDetail = event.target.value;
              setDetail(nextDetail);

              if (voiceReview) {
                const nextReview = createVoiceTranscriptReview(
                  nextDetail,
                  profile.name,
                );
                setVoiceReview({
                  ...nextReview,
                  recognizedText: nextDetail,
                  confirmedText: nextDetail,
                  confirmed: false,
                });
              }

              if (error) {
                setError("");
              }
              if (savedId) {
                setSavedId(null);
              }
              if (saveMessage) {
                setSaveMessage("");
              }
              if (lastSavedPreview && nextDetail.trim()) {
                setLastSavedPreview(null);
              }
            }}
            placeholder={inputPlaceholders[inputMode]}
            value={detail}
          />
          {error ? (
            <p className="mt-3 text-sm font-semibold text-[#be4c3c]">{error}</p>
          ) : null}
          {savedId ? (
            <div className="mt-3 flex items-center justify-between rounded-2xl bg-[#edf8ed] px-4 py-3 text-sm">
              <span className="inline-flex items-center gap-2 font-bold text-[#16804b]">
                <PetIcon className="h-4 w-4" name="check" />
                {saveMessage || "기록이 저장되었습니다."}
              </span>
              <Link className="font-bold text-[#0f6e3e]" href="/timeline">
                타임라인 보기
              </Link>
            </div>
          ) : null}
        </Card>

        <section>
          <SectionHeader title="AI 구조화 미리보기" />
          <div className="space-y-3">
            <Card
              className={`p-4 ${showPreviewLoading ? "pet-log-loading-border" : ""}`}
              motion="rise"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`grid h-8 w-8 place-items-center rounded-full ${
                        showPreviewLoading
                          ? "pet-log-pulse-dot bg-[#edf8ed] text-[#16804b]"
                          : "bg-[#edf8ed] text-[#16804b]"
                      }`}
                    >
                      <PetIcon className="h-4 w-4" name="sparkle" />
                    </span>
                    <CategoryBadge category={activeDisplayCategory} />
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                        activeDisplayNeedsConfirmation
                          ? "bg-[#fff2df] text-[#a4651a]"
                          : "bg-[#e8f5df] text-[#32783c]"
                      }`}
                    >
                      {showPreviewLoading
                        ? "AI 확인 중"
                        : `신뢰도 ${activeDisplayConfidence}%`}
                    </span>
                  </div>
                  <h3 className="mt-2 text-sm font-bold text-[#1f2922]">
                    {activeDisplaySummary || previewTitle}
                  </h3>
                  <p className="mt-1 text-xs leading-5 text-[#6c7667]">
                    {(isShowingSavedPreview
                      ? savedPreviewMessage
                      : visiblePreviewError) ||
                      (activeDisplayNeedsConfirmation
                        ? "AI 분류가 애매합니다. 카테고리와 내용을 확인한 뒤 저장해주세요."
                        : "입력한 내용이 구조화되어 저장됩니다. 필요하면 저장 전 수정할 수 있습니다.")}
                  </p>
                </div>
                <span className="text-sm font-bold text-[#16804b]">
                  {categoryLabels[activeDisplayCategory]}
                </span>
              </div>

              {category !== "all" && activeDisplayCategory !== category ? (
                <button
                  className="pet-log-pressable mt-3 h-10 w-full rounded-xl border border-[#cfe2cd] bg-[#f4faf2] text-sm font-bold text-[#16804b]"
                  onClick={() => setCategory(activeDisplayCategory)}
                  type="button"
                >
                  AI 추천 분류 적용
                </button>
              ) : null}

              <div className="mt-3 flex flex-wrap gap-2">
                {detectedCategories.map((detectedCategory) => {
                  const isSelected = activeDisplayCategory === detectedCategory;

                  return (
                    <button
                      className={`pet-log-pressable inline-flex h-7 items-center rounded-full px-2.5 text-[11px] font-black leading-none transition-colors ${
                        categoryBadgeColors[detectedCategory]
                      } ${isSelected ? "ring-2 ring-[#16804b]/30 ring-offset-1" : "opacity-90"}`}
                      key={detectedCategory}
                      onClick={() => setPreviewTab(detectedCategory)}
                      type="button"
                    >
                      {categoryLabels[detectedCategory]}
                    </button>
                  );
                })}
              </div>

              <div className="mt-3 grid grid-cols-1 gap-2">
                {activeDisplayMeasurements.length > 0 ? (
                  activeDisplayMeasurements.map((measurement) => (
                    <div
                      className="rounded-xl bg-[#f4f7f0] px-3 py-2"
                      key={`${measurement.label}-${measurement.value}`}
                    >
                      <p className="text-[11px] font-bold text-[#7b8576]">
                        {measurement.label}
                      </p>
                      <p className="mt-1 break-keep text-sm font-black leading-5 text-[#1f2922]">
                        {measurement.value}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="rounded-xl bg-[#f4f7f0] px-3 py-2">
                    <p className="text-[11px] font-bold text-[#7b8576]">
                      {categoryLabels[activeDisplayCategory]}
                    </p>
                    <p className="mt-1 text-sm font-black leading-5 text-[#1f2922]">
                      {activeDisplaySummary || "카테고리별 내용이 없습니다."}
                    </p>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </section>

        <section>
          <SectionHeader title="최근 기록" />
          <div className="space-y-2">
            {recentRecordGroups.map((group) => (
              <Card className="p-3" key={group.id} motion="rise">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap gap-1.5">
                      {group.categories.map((category) => (
                        <CategoryBadge category={category} key={category} />
                      ))}
                    </div>
                    <h3 className="mt-2 truncate text-sm font-bold text-[#1f2922]">
                      {group.records.length > 1
                        ? `${group.records.length}개 기록`
                        : group.records[0]
                          ? normalizeRecentRecordTitle(group.records[0])
                          : "기록"}
                    </h3>
                    <div className="mt-2 space-y-1.5">
                      {group.records.map((record) => (
                        <div
                          className="rounded-xl bg-[#f7faf4] px-3 py-2"
                          key={record.id}
                        >
                          <p className="text-xs font-black text-[#1f2922]">
                            {normalizeRecentRecordTitle(record)}
                          </p>
                          <p className="mt-0.5 line-clamp-2 text-xs leading-5 text-[#6c7667]">
                            {normalizeRecentRecordDetail(record)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <span className="shrink-0 text-xs font-bold text-[#8a9286]">
                    {group.time}
                  </span>
                </div>
              </Card>
            ))}
            {recentRecordGroups.length === 0 ? (
              <Card className="p-4 text-center" motion="rise">
                <p className="text-sm font-bold text-[#1f2922]">
                  아직 최근 기록이 없습니다.
                </p>
                <p className="mt-1 text-xs leading-5 text-[#667262]">
                  첫 기록을 저장하면 여기에 바로 표시됩니다.
                </p>
              </Card>
            ) : null}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PetIcon } from "@/components/pet-icons";
import { usePetLog } from "@/components/pet-log-provider";
import { Card, CategoryBadge, SectionHeader } from "@/components/ui";
import { structureRecordPreview, transcribeSpeechAudio } from "@/lib/api-client";
import { categoryLabels } from "@/lib/record-constants";
import {
  defaultRecordCategoryChoice,
  getBrowserSpeechRecognitionConstructor,
  getInputModeFeedback,
  getRecordCategoryChoiceLabel,
  recordCategoryChoiceOptions,
  resolveRecordCategoryForSave,
  type BrowserSpeechRecognition,
  type BrowserSpeechRecognitionConstructor,
  type BrowserSpeechRecognitionResultEvent,
  type RecordInputMode,
} from "@/lib/record-input";
import type { RecordCategoryChoice, StructuredRecord } from "@/lib/types";

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
};

function createPendingPreview(detail: string, category: RecordCategoryChoice): StructuredRecord {
  const sourceText = detail.trim();
  const firstSentence = sourceText.split(/\n|[.!?。]/)[0]?.trim() ?? sourceText;
  const suggestedCategory = category === "all" ? "meal" : category;
  return {
    sourceText,
    normalizedSummary: firstSentence ? (firstSentence.length > 38 ? `${firstSentence.slice(0, 38)}...` : firstSentence) : "기록 내용을 입력하면 미리보기가 생성됩니다.",
    suggestedCategory,
    detectedCategories: [suggestedCategory],
    confidence: 0.4,
    measurements: [],
    needsConfirmation: true,
  };
}

export default function RecordPage() {
  const { addRecord, profile, records } = usePetLog();
  const [detail, setDetail] = useState("");
  const [category, setCategory] = useState<RecordCategoryChoice>(defaultRecordCategoryChoice);
  const [inputMode, setInputMode] = useState<RecordInputMode>("voice");
  const [error, setError] = useState("");
  const [savedId, setSavedId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [aiPreview, setAiPreview] = useState<AiPreviewResult | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const speechRecognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const mediaStreamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    console.log("[record/page] records 업데이트:", records.length, "건", records.slice(0, 3).map((r) => r.id));
  }, [records]);

  const preview = records.slice(0, 3);
  const trimmedDetail = detail.trim();
  const hasActivePet = !!profile.id;
  const isInvalid = trimmedDetail.length < 5 || trimmedDetail.length > maxLength;
  const fallbackPreview = useMemo(() => createPendingPreview(trimmedDetail, category), [category, trimmedDetail]);
  const activePreview = aiPreview?.detail === trimmedDetail && aiPreview.category === category ? aiPreview.structured : null;
  const displayPreview = activePreview ?? fallbackPreview;
  const resolvedCategory = resolveRecordCategoryForSave(category, displayPreview);
  const showPreviewLoading = !!trimmedDetail && isPreviewLoading && !activePreview;
  const visiblePreviewError = trimmedDetail ? previewError : "";
  const confidencePercent = Math.round(displayPreview.confidence * 100);
  const modeFeedback = getInputModeFeedback(inputMode);
  const detectedCategories = displayPreview.detectedCategories?.length
    ? displayPreview.detectedCategories
    : [displayPreview.suggestedCategory];

  const previewTitle = useMemo(() => {
    if (!trimmedDetail) {
      return "기록 내용을 입력하면 미리보기가 생성됩니다.";
    }
    return trimmedDetail.length > 28 ? `${trimmedDetail.slice(0, 28)}...` : trimmedDetail;
  }, [trimmedDetail]);

  useEffect(() => {
    if (!trimmedDetail || !hasActivePet) {
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(() => {
      setIsPreviewLoading(true);
      structureRecordPreview({ detail: trimmedDetail, fallbackCategory: category })
        .then((response) => {
          if (!cancelled) {
            console.log("[record/page] AI 미리보기 성공:", response.structured.suggestedCategory, Math.round(response.structured.confidence * 100) + "%");
            setAiPreview({ category, detail: trimmedDetail, structured: response.structured });
            setPreviewError("");
          }
        })
        .catch((err: unknown) => {
          if (!cancelled) {
            console.log("[record/page] AI 미리보기 실패:", err instanceof Error ? err.message : err);
            setAiPreview(null);
            setPreviewError("AI 미리보기를 불러오지 못해 기본 분류로 표시합니다.");
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
  }, [category, hasActivePet, trimmedDetail]);

  useEffect(() => {
    return () => {
      speechRecognitionRef.current?.stop();
      stopMediaStream();
    };
  }, []);

  function stopMediaStream() {
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
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
      return;
    }

    if (trimmedDetail.length < 5) {
      setError("기록은 5자 이상 입력해주세요.");
      setSavedId(null);
      return;
    }

    if (trimmedDetail.length > maxLength) {
      setError(`기록은 ${maxLength}자 이내로 입력해주세요.`);
      setSavedId(null);
      return;
    }

    setIsSaving(true);
    try {
      if (category === "all" && !activePreview) {
        try {
          const response = await structureRecordPreview({ detail: trimmedDetail, fallbackCategory: category });
          console.log("[record/page] structureRecordPreview 성공:", response.structured.suggestedCategory);
          setAiPreview({ category, detail: trimmedDetail, structured: response.structured });
          setPreviewError("");
        } catch (err) {
          console.log("[record/page] structureRecordPreview 실패:", err instanceof Error ? err.message : err);
          setPreviewError("AI 미리보기를 불러오지 못했습니다. 저장 시 서버에서 다시 처리합니다.");
        }
      }

      console.log("[record/page] addRecord 호출:", category, trimmedDetail.slice(0, 30));
      const record = await addRecord({ category, detail: trimmedDetail });
      console.log("[record/page] addRecord 성공:", record.id);
      setSavedId(record.id);
      setError("");
      setDetail("");
    } catch (err) {
      console.log("[record/page] addRecord 실패:", err instanceof Error ? err.message : err);
      setSavedId(null);
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
      console.log("[record/page] transcribeSpeechAudio 호출:", fileType, audio.size, "bytes");
      const transcription = await transcribeSpeechAudio(file);
      console.log("[record/page] transcribeSpeechAudio 성공:", transcription.text.slice(0, 50));
      setDetail(transcription.text);
    } catch (err) {
      console.log("[record/page] transcribeSpeechAudio 실패:", err instanceof Error ? err.message : err);
      setError("음성 인식에 실패했습니다. 텍스트로 직접 입력해주세요.");
    } finally {
      setIsTranscribing(false);
    }
  }

  function applySpeechRecognitionResult(event: BrowserSpeechRecognitionResultEvent) {
    const transcriptParts: string[] = [];
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const transcript = event.results[index]?.[0]?.transcript.trim();
      if (transcript) {
        transcriptParts.push(transcript);
      }
    }
    const transcript = transcriptParts.join(" ").trim();
    if (transcript) {
      setDetail((currentDetail) => {
        const current = currentDetail.trim();
        return current ? `${current} ${transcript}` : transcript;
      });
    }
  }

  function startBrowserSpeechRecognition(SpeechRecognition: BrowserSpeechRecognitionConstructor) {
    const recognition = new SpeechRecognition();
    recognition.lang = "ko-KR";
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.onresult = applySpeechRecognitionResult;
    recognition.onerror = () => {
      speechRecognitionRef.current = null;
      setIsRecording(false);
      setError("브라우저 음성 인식에 실패했습니다. 다시 녹음하거나 텍스트로 입력해주세요.");
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
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
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
        const audio = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
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
    const SpeechRecognition = getBrowserSpeechRecognitionConstructor();
    if (SpeechRecognition) {
      setError("");
      setSavedId(null);
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
            isInvalid ? "bg-[#8ab99f]" : "bg-[#16804b]"
          }`}
          disabled={isSaving || !hasActivePet}
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
        <Card className="bg-gradient-to-br from-white to-[#edf8ed]" motion="rise">
          <p className="inline-flex items-center gap-1.5 text-sm font-bold text-[#16804b]">
            <PetIcon className="h-4 w-4" name="sparkle" />
            기록 준비
          </p>
          <h2 className="mt-1 text-lg font-black text-[#1f2922]">오늘 케어 내용을 한 번에 정리해요</h2>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <p className="text-[11px] font-bold text-[#778174]">분류</p>
              <p className="mt-1 truncate text-sm font-black text-[#1f2922]">{getRecordCategoryChoiceLabel(category)}</p>
            </div>
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <p className="text-[11px] font-bold text-[#778174]">AI 신뢰도</p>
              <p className="mt-1 text-sm font-black text-[#1f2922]">{confidencePercent}%</p>
            </div>
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <p className="text-[11px] font-bold text-[#778174]">입력</p>
              <p className="mt-1 text-sm font-black text-[#1f2922]">{detail.length}/{maxLength}</p>
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
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${active ? "bg-white/20" : "bg-[#f4f7f0] text-[#16804b]"}`}>
                    <PetIcon className="h-5 w-5" name={active ? "check" : item.icon} />
                  </span>
                  <span className="min-w-0">
                    <span className="block">{item.label}</span>
                    <span className={`mt-1 block text-[11px] font-semibold ${active ? "text-white/80" : "text-[#7c8777]"}`}>
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
              <p className="mt-1 text-xs font-semibold text-[#7c8777]">현재 저장은 텍스트 메모 기준으로 동작합니다.</p>
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
                    active ? "border-[#16804b] bg-[#e7f4eb] text-[#0b7a43]" : "border-[#dce5d5] bg-white text-[#40513f]"
                  }`}
                  key={mode.value}
                  onClick={() => setInputMode(mode.value)}
                  type="button"
                >
                  <span className="block">{mode.label}</span>
                  <span className="mt-1 block text-[11px] font-semibold opacity-80">{feedback.label}</span>
                </button>
              );
            })}
          </div>
          <div
            className={`mt-3 rounded-2xl px-4 py-3 ${
              modeFeedback.status === "available" ? "bg-[#edf8ed] text-[#356342]" : "bg-[#fff7ed] text-[#7a5531]"
            }`}
          >
            <p className="text-xs font-bold">{modeFeedback.label}</p>
            <p className="mt-1 text-xs leading-5">{modeFeedback.detail}</p>
          </div>
          {inputMode === "voice" ? (
            <button
              className={`pet-log-pressable mt-3 flex min-h-12 w-full items-center justify-center rounded-xl border px-4 text-sm font-bold ${
                isRecording ? "border-[#be4c3c] bg-[#fff1ee] text-[#be4c3c]" : "border-[#cfe2cd] bg-white text-[#16804b]"
              }`}
              disabled={isTranscribing}
              onClick={handleRecordingButtonClick}
              type="button"
            >
              {isTranscribing ? "음성 변환 중" : isRecording ? "녹음 종료" : "녹음 시작"}
            </button>
          ) : null}
        </Card>

        <Card motion="rise">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-bold">자연어 기록</h2>
            <span className={`text-xs font-semibold ${detail.length > maxLength ? "text-[#be4c3c]" : "text-[#9aa494]"}`}>
              {detail.length}/{maxLength}
            </span>
          </div>
          <textarea
            className="min-h-40 w-full resize-none rounded-2xl border border-[#dde6d6] bg-[#fbfcfa] p-4 text-sm leading-6 outline-none placeholder:text-[#8a9286] focus:border-[#16804b] focus:ring-2 focus:ring-[#16804b]/15"
            maxLength={maxLength + 40}
            onChange={(event) => {
              setDetail(event.target.value);
              if (error) {
                setError("");
              }
              if (savedId) {
                setSavedId(null);
              }
            }}
            placeholder={inputPlaceholders[inputMode]}
            value={detail}
          />
          {error ? <p className="mt-3 text-sm font-semibold text-[#be4c3c]">{error}</p> : null}
          {savedId ? (
            <div className="mt-3 flex items-center justify-between rounded-2xl bg-[#edf8ed] px-4 py-3 text-sm">
              <span className="inline-flex items-center gap-2 font-bold text-[#16804b]">
                <PetIcon className="h-4 w-4" name="check" />
                기록이 저장되었습니다.
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
            <Card className={`p-4 ${showPreviewLoading ? "pet-log-loading-border" : ""}`} motion="rise">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`grid h-8 w-8 place-items-center rounded-full ${showPreviewLoading ? "pet-log-pulse-dot bg-[#edf8ed] text-[#16804b]" : "bg-[#edf8ed] text-[#16804b]"}`}>
                      <PetIcon className="h-4 w-4" name="sparkle" />
                    </span>
                    <CategoryBadge category={displayPreview.suggestedCategory} />
                    <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${displayPreview.needsConfirmation ? "bg-[#fff2df] text-[#a4651a]" : "bg-[#e8f5df] text-[#32783c]"}`}>
                      {showPreviewLoading ? "AI 확인 중" : `신뢰도 ${confidencePercent}%`}
                    </span>
                  </div>
                  <h3 className="mt-2 text-sm font-bold text-[#1f2922]">{displayPreview.normalizedSummary || previewTitle}</h3>
                  <p className="mt-1 text-xs leading-5 text-[#6c7667]">
                    {visiblePreviewError ||
                    (displayPreview.needsConfirmation
                      ? "AI 분류가 애매합니다. 카테고리와 내용을 확인한 뒤 저장해주세요."
                      : "입력한 내용이 구조화되어 저장됩니다. 필요하면 저장 전 수정할 수 있습니다.")}
                  </p>
                </div>
              </div>
              {category !== "all" && displayPreview.suggestedCategory !== category ? (
                <button
                  className="pet-log-pressable mt-3 h-10 w-full rounded-xl border border-[#cfe2cd] bg-[#f4faf2] text-sm font-bold text-[#16804b]"
                  onClick={() => setCategory(displayPreview.suggestedCategory)}
                  type="button"
                >
                  AI 추천 분류 적용
                </button>
              ) : null}
              {detectedCategories.filter((cat) => cat !== displayPreview.suggestedCategory).length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {detectedCategories
                    .filter((cat) => cat !== displayPreview.suggestedCategory)
                    .map((detectedCategory) => (
                      <span
                        className="rounded-full bg-[#f4f7f0] px-2.5 py-1 text-xs font-bold text-[#53604f]"
                        key={detectedCategory}
                      >
                        {categoryLabels[detectedCategory]}
                      </span>
                    ))}
                </div>
              )}
              <div className="mt-3 grid grid-cols-2 gap-2">
                {displayPreview.measurements.length > 0 ? (
                  displayPreview.measurements.map((measurement) => (
                    <div className="rounded-xl bg-[#f4f7f0] px-3 py-2" key={`${measurement.label}-${measurement.value}`}>
                      <p className="text-[11px] font-bold text-[#7b8576]">{measurement.label}</p>
                      <p className="mt-1 text-sm font-black text-[#1f2922]">{measurement.value}</p>
                    </div>
                  ))
                ) : (
                  <div className="col-span-2 rounded-xl bg-[#f4f7f0] px-3 py-2">
                    <p className="text-xs font-semibold leading-5 text-[#667262]">추출된 수치가 없습니다. 필요하면 g, kg, 분, 회 같은 단위를 함께 적어주세요.</p>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </section>

        <section>
          <SectionHeader title="최근 기록" />
          <div className="space-y-2">
            {preview.map((record) => (
              <Card className="p-3" key={record.id} motion="rise">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <CategoryBadge category={record.category} />
                    <h3 className="mt-2 truncate text-sm font-bold text-[#1f2922]">{record.title}</h3>
                    <p className="mt-1 line-clamp-2 text-xs leading-5 text-[#6c7667]">{record.detail}</p>
                  </div>
                  <span className="text-xs font-bold text-[#8a9286]">{record.time}</span>
                </div>
              </Card>
            ))}
            {preview.length === 0 ? (
              <Card className="p-4 text-center" motion="rise">
                <p className="text-sm font-bold text-[#1f2922]">아직 최근 기록이 없습니다.</p>
                <p className="mt-1 text-xs leading-5 text-[#667262]">첫 기록을 저장하면 여기에 바로 표시됩니다.</p>
              </Card>
            ) : null}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

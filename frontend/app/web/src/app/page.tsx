"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { usePetLog } from "@/components/pet-log-provider";
import { AiMascot, Card, CategoryBadge, SectionHeader } from "@/components/ui";
import { getRecentChange, getRecordStatusLabel, getTodaySummary, type HomeSummaryTone } from "@/lib/home-summary";
import { PetIcon } from "@/components/pet-icons";
import { sendChatbotMessage } from "@/lib/api-client";
import { sortCareNotificationsByLatest } from "@/lib/notifications";
import type { ChatbotThread } from "@/lib/types";

type SpeechRecognitionEventLike = {
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string;
      };
    };
  };
};

type SpeechRecognitionErrorLike = {
  error?: string;
};

type PetLogSpeechRecognition = {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onend: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorLike) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  start: () => void;
};

type PetLogSpeechRecognitionConstructor = new () => PetLogSpeechRecognition;

declare global {
  interface Window {
    SpeechRecognition?: PetLogSpeechRecognitionConstructor;
    webkitSpeechRecognition?: PetLogSpeechRecognitionConstructor;
  }
}

const toneText: Record<HomeSummaryTone, string> = {
  green: "text-[#16804b]",
  orange: "text-[#a4651a]",
  red: "text-[#be4c3c]",
  blue: "text-[#356aa8]",
};

const toneDot: Record<HomeSummaryTone, string> = {
  green: "bg-[#16804b]",
  orange: "bg-[#d38a2d]",
  red: "bg-[#be4c3c]",
  blue: "bg-[#356aa8]",
};

const toneCard: Record<HomeSummaryTone, string> = {
  green: "border-[#d8ead1] bg-[#fbfff8]",
  orange: "border-[#f1d9af] bg-[#fffaf0]",
  red: "border-[#f0cbc5] bg-[#fff7f5]",
  blue: "border-[#d4e0f5] bg-[#f6f9ff]",
};

const homeNotificationBorderClasses: Partial<Record<HomeSummaryTone, string>> = {
  orange: "pet-log-notification-alert-border pet-log-notification-alert-border-orange",
  red: "pet-log-notification-alert-border pet-log-notification-alert-border-red",
};

const chatbotQuestions: Array<{ icon: "heart" | "bell" | "syringe"; text: string }> = [
  { icon: "heart", text: "오늘 상태 괜찮아?" },
  { icon: "bell", text: "주의 알림은 왜 떴어?" },
  { icon: "syringe", text: "백신 전에 확인할 게 있어?" },
];

const petChatQuestions = ["오늘 기분 어때?", "밥은 맛있었어?", "산책 또 가고 싶어?"];
const panelAnimationMs = 180;

type PetChatMessage = {
  id: string;
  role: "user" | "pet";
  content: string;
};

export default function Home() {
  const { profile, records, schedules, settings, insights, suggestions, isAnalysisLoading, notifications } = usePetLog();
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);
  const [isPetChatOpen, setIsPetChatOpen] = useState(false);
  const [chatbotQuestion, setChatbotQuestion] = useState("");
  const [chatbotNotice, setChatbotNotice] = useState("");
  const [petChatInput, setPetChatInput] = useState("");
  const [petChatNotice, setPetChatNotice] = useState("");
  const [petChatMessages, setPetChatMessages] = useState<PetChatMessage[]>([]);
  const [isChatbotSending, setIsChatbotSending] = useState(false);
  const [isChatbotHistoryLoading] = useState(false);
  const [isVoiceListening, setIsVoiceListening] = useState(false);
  const [isPetVoiceListening, setIsPetVoiceListening] = useState(false);
  const [closingPanel, setClosingPanel] = useState<"chatbot" | "pet" | null>(null);
  const [chatbotThread, setChatbotThread] = useState<ChatbotThread | null>(null);
  const chatbotScrollRef = useRef<HTMLDivElement | null>(null);
  const petChatScrollRef = useRef<HTMLDivElement | null>(null);
  const petChatMessageIdRef = useRef(0);
  const panelCloseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestRecords = records.slice(0, 3);
  const homeNotifications = useMemo(() => sortCareNotificationsByLatest(notifications).slice(0, 2), [notifications]);
  const todaySummary = getTodaySummary(records);
  
  // AI Insights mapping (Replacing legacy recentChange)
  const topInsight = insights[0];
  const severityToTone: Record<string, HomeSummaryTone> = {
    alert: "red",
    notice: "orange",
    info: "green"
  };
  
  const recentChange = useMemo(() => {
    if (topInsight) {
      return {
        label: `AI 분석 · ${topInsight.severity === "alert" ? "주의" : topInsight.severity === "notice" ? "변화" : "안정"}`,
        title: topInsight.title,
        detail: topInsight.reason,
        tone: severityToTone[topInsight.severity] || "green"
      };
    }
    return getRecentChange(records);
  }, [topInsight, records]);

  // AI Suggestions mapping (Replacing legacy getAiCareSuggestions)
  const homeSuggestions = useMemo(() => {
    if (!settings.aiInsightEnabled) return [];
    return suggestions.slice(0, 2).map((s, idx) => ({
      id: `suggestion-${idx}`,
      category: "케어 가이드" as const,
      title: s.title,
      detail: s.reason,
      action: s.action,
      actionHref: s.action.includes("타임라인") ? "/timeline" : "/record",
      tone: "green" as const
    }));
  }, [suggestions, settings.aiInsightEnabled]);

  const pendingSchedules = schedules.filter((schedule) => !schedule.isDone).length;
  const chatbotMessageCount = chatbotThread?.messages.length ?? 0;
  const petChatMessageCount = petChatMessages.length;

  useEffect(() => {
    if (!isChatbotOpen) {
      return;
    }

    const frameId = requestAnimationFrame(() => {
      const scrollContainer = chatbotScrollRef.current;
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    });

    return () => cancelAnimationFrame(frameId);
  }, [chatbotMessageCount, chatbotNotice, isChatbotHistoryLoading, isChatbotOpen]);

  useEffect(() => {
    if (!isPetChatOpen) {
      return;
    }

    const frameId = requestAnimationFrame(() => {
      const scrollContainer = petChatScrollRef.current;
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    });

    return () => cancelAnimationFrame(frameId);
  }, [isPetChatOpen, petChatMessageCount, petChatNotice]);

  function clearPanelCloseTimer() {
    if (panelCloseTimerRef.current) {
      clearTimeout(panelCloseTimerRef.current);
      panelCloseTimerRef.current = null;
    }
  }

  function closeChatbot() {
    if (closingPanel === "chatbot") {
      return;
    }
    clearPanelCloseTimer();
    setClosingPanel("chatbot");
    panelCloseTimerRef.current = setTimeout(() => {
      setIsChatbotOpen(false);
      setClosingPanel((current) => (current === "chatbot" ? null : current));
      panelCloseTimerRef.current = null;
    }, panelAnimationMs);
  }

  function openPetChat() {
    clearPanelCloseTimer();
    setClosingPanel(null);
    setIsChatbotOpen(false);
    setIsPetChatOpen(true);
  }

  function closePetChat() {
    if (closingPanel === "pet") {
      return;
    }
    clearPanelCloseTimer();
    setClosingPanel("pet");
    panelCloseTimerRef.current = setTimeout(() => {
      setIsPetChatOpen(false);
      setClosingPanel((current) => (current === "pet" ? null : current));
      panelCloseTimerRef.current = null;
    }, panelAnimationMs);
  }

  async function askChatbot(question: string) {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setChatbotNotice("궁금한 내용을 입력하거나 추천 질문을 선택해주세요.");
      return;
    }

    setIsChatbotSending(true);
    try {
      const response = await sendChatbotMessage(
        trimmedQuestion,
        latestRecords.map((record) => record.id),
        chatbotThread?.id,
      );
      setChatbotThread(response.thread ?? chatbotThread);
      setChatbotNotice("");
      setChatbotQuestion((current) => (current.trim() === trimmedQuestion ? "" : current));
    } catch {
      setChatbotNotice("답변을 불러오지 못했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setIsChatbotSending(false);
    }
  }

  function selectChatbotQuestion(question: string) {
    setChatbotQuestion(question);
    void askChatbot(question);
  }

  function submitChatbotQuestion() {
    void askChatbot(chatbotQuestion);
  }

  function createPetReply(question: string) {
    const latestRecord = latestRecords[0];
    const lowerQuestion = question.toLowerCase();
    const healthConcern = /아파|토|설사|혈변|기침|숨|호흡|통증|병원|약/.test(question);

    if (healthConcern) {
      return `나를 걱정해줘서 고마워. 아픈지 단정하긴 어려우니까 오늘 상태를 기록하고, 계속 반복되거나 심해지면 병원에 물어봐줘.`;
    }

    if (question.includes("밥") || question.includes("먹")) {
      return latestRecord?.category === "meal"
        ? `아까 ${latestRecord.title} 기록 봤지? 나는 규칙적으로 챙겨주면 마음이 편해.`
        : `밥 얘기하니까 기대된다. 먹은 양도 짧게 기록해주면 내 컨디션을 더 잘 알 수 있어.`;
    }

    if (question.includes("산책") || lowerQuestion.includes("walk")) {
      return latestRecord?.category === "walk"
        ? `오늘 산책 기억나. 밖 냄새 맡는 시간이 참 좋아. 다음에도 천천히 같이 걸어줘.`
        : `산책 얘기만 들어도 신나. 짧게라도 같이 나가면 기분이 좋아질 것 같아.`;
    }

    if (question.includes("기분") || question.includes("좋아")) {
      return `지금은 네가 말을 걸어줘서 좋아. 오늘 있었던 일을 조금씩 남겨주면 내가 어떤 하루를 보냈는지 더 잘 전할 수 있어.`;
    }

    return latestRecord
      ? `${latestRecord.title} 기록을 보니까 오늘도 네가 나를 잘 챙겨준 것 같아. 또 궁금한 거 있으면 나한테 말 걸어줘.`
      : `아직 오늘 기록이 많지는 않지만, 네가 말 걸어줘서 좋아. 밥, 산책, 배변 같은 걸 남겨주면 더 내 얘기처럼 답할 수 있어.`;
  }

  function sendPetChatMessage(question: string) {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setPetChatNotice(`${profile.name}에게 하고 싶은 말을 입력해주세요.`);
      return;
    }

    petChatMessageIdRef.current += 1;
    const messageId = petChatMessageIdRef.current;
    const userMessage: PetChatMessage = {
      id: `pet-user-${messageId}`,
      role: "user",
      content: trimmedQuestion,
    };
    const petMessage: PetChatMessage = {
      id: `pet-reply-${messageId}`,
      role: "pet",
      content: createPetReply(trimmedQuestion),
    };

    setPetChatMessages((current) => [...current, userMessage, petMessage].slice(-12));
    setPetChatInput("");
    setPetChatNotice("");
  }

  function selectPetChatQuestion(question: string) {
    setPetChatInput(question);
    sendPetChatMessage(question);
  }

  function submitPetChatQuestion() {
    sendPetChatMessage(petChatInput);
  }

  function startChatbotVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setChatbotNotice("이 브라우저에서는 음성 입력을 지원하지 않습니다.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "ko-KR";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = (event) => {
        const transcript = event.results[0]?.[0]?.transcript.trim();
        if (!transcript) {
          return;
        }
        setChatbotQuestion((current) => {
          const trimmedCurrent = current.trim();
          return trimmedCurrent ? `${trimmedCurrent} ${transcript}` : transcript;
        });
        setChatbotNotice("");
      };
      recognition.onerror = (event) => {
        const message = event.error === "not-allowed" ? "마이크 권한을 허용해야 음성 입력을 사용할 수 있습니다." : "음성을 인식하지 못했습니다. 다시 시도해주세요.";
        setChatbotNotice(message);
      };
      recognition.onend = () => {
        setIsVoiceListening(false);
      };
      setIsVoiceListening(true);
      recognition.start();
    } catch {
      setIsVoiceListening(false);
      setChatbotNotice("음성 입력을 시작하지 못했습니다. 다시 시도해주세요.");
    }
  }

  function startPetChatVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setPetChatNotice("이 브라우저에서는 음성 입력을 지원하지 않습니다.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "ko-KR";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = (event) => {
        const transcript = event.results[0]?.[0]?.transcript.trim();
        if (!transcript) {
          return;
        }
        setPetChatInput((current) => {
          const trimmedCurrent = current.trim();
          return trimmedCurrent ? `${trimmedCurrent} ${transcript}` : transcript;
        });
        setPetChatNotice("");
      };
      recognition.onerror = (event) => {
        const message = event.error === "not-allowed" ? "마이크 권한을 허용해야 음성 입력을 사용할 수 있습니다." : "음성을 인식하지 못했습니다. 다시 시도해주세요.";
        setPetChatNotice(message);
      };
      recognition.onend = () => {
        setIsPetVoiceListening(false);
      };
      setIsPetVoiceListening(true);
      recognition.start();
    } catch {
      setIsPetVoiceListening(false);
      setPetChatNotice("음성 입력을 시작하지 못했습니다. 다시 시도해주세요.");
    }
  }

  return (
    <AppShell
      action={
        <Link
          aria-label="기록 추가"
          className="pet-log-pressable grid h-10 w-10 place-items-center rounded-full bg-[#16804b] text-white shadow-sm"
          href="/record"
        >
          <PetIcon className="h-5 w-5" name="plus" />
        </Link>
      }
      subtitle="AI가 먼저 케어해주는 홈"
      title={`${profile.name}의 오늘`}
    >
      <div className="space-y-5">
        <Card className="relative overflow-hidden p-4" motion="rise">
          <div className="absolute right-0 -top-12 h-24 w-24 rounded-full bg-[#e9f6df]" />
          <div className="relative grid grid-cols-[52px_1fr_auto] items-center gap-3">
            <div className="grid h-12 w-12 place-items-center overflow-hidden rounded-2xl bg-[#eaf5e5] text-xl font-black text-[#16804b]">
              {profile.photoDataUrl ? (
                <Image
                  alt={`${profile.name} 프로필 사진`}
                  className="h-full w-full object-cover"
                  height={48}
                  src={profile.photoDataUrl}
                  unoptimized
                  width={48}
                />
              ) : (
                profile.name.slice(0, 1)
              )}
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-base font-black text-[#1f2922]">{profile.name}</p>
                <span className="rounded-full bg-[#f0f3ed] px-2.5 py-1 text-[11px] font-bold text-[#5e6859]">
                  {profile.breed}
                </span>
                <span className="rounded-full bg-[#f0f3ed] px-2.5 py-1 text-[11px] font-bold text-[#5e6859]">
                  {profile.age}
                </span>
              </div>
              <p className="mt-2 truncate text-sm font-semibold text-[#667262]">
                {profile.weight} · {profile.notes[0] ?? profile.personality}
              </p>
            </div>
            <Link className="rounded-full bg-[#edf8ed] px-3 py-2 text-xs font-black text-[#16804b]" href="/profile">
              보기
            </Link>
          </div>
          <div className="relative mt-4 grid grid-cols-3 gap-2">
            <div className="rounded-2xl bg-[#f4f7f0] px-3 py-3 text-center">
              <PetIcon className="mx-auto h-4 w-4 text-[#16804b]" name="record" />
              <p className="text-[11px] font-bold text-[#778174]">최근 기록</p>
              <p className="mt-1 text-base font-black text-[#1f2922]">{latestRecords.length}</p>
            </div>
            <div className="rounded-2xl bg-[#fffaf0] px-3 py-3 text-center">
              <PetIcon className="mx-auto h-4 w-4 text-[#a4651a]" name="bell" />
              <p className="text-[11px] font-bold text-[#778174]">오늘 알림</p>
              <p className="mt-1 text-base font-black text-[#1f2922]">{notifications.length}</p>
            </div>
            <div className="rounded-2xl bg-[#f6f9ff] px-3 py-3 text-center">
              <PetIcon className="mx-auto h-4 w-4 text-[#356aa8]" name="schedule" />
              <p className="text-[11px] font-bold text-[#778174]">일정</p>
              <p className="mt-1 text-base font-black text-[#1f2922]">{pendingSchedules}</p>
            </div>
          </div>
        </Card>

        <Card className="overflow-hidden border-[#d8e8d1] bg-[#fffdf7] p-0" motion="rise">
          <div className="bg-[linear-gradient(135deg,#fffdf7_0%,#eef8ec_58%,#f6fbff_100%)] p-4">
            <div className="flex items-start gap-3">
              <div className="grid h-12 w-12 shrink-0 place-items-center overflow-hidden rounded-2xl bg-white text-lg font-black text-[#16804b] shadow-inner">
                {profile.photoDataUrl ? (
                  <Image
                    alt={`${profile.name} 프로필 사진`}
                    className="h-full w-full object-cover"
                    height={48}
                    src={profile.photoDataUrl}
                    unoptimized
                    width={48}
                  />
                ) : (
                  profile.name.slice(0, 1)
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-black text-[#16804b]">{profile.name}와 대화</p>
                <h2 className="mt-1 text-lg font-black leading-7 text-[#1f2922]">오늘은 나한테 직접 물어봐</h2>
                <p className="mt-2 text-sm font-semibold leading-6 text-[#667262]">
                  최근 기록과 성격을 바탕으로 {profile.name}가 말하는 듯 답해요.
                </p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {petChatQuestions.slice(0, 2).map((question) => (
                <button
                  className="pet-log-pressable h-9 rounded-full border border-[#d8e6d2] bg-white px-3 text-xs font-bold text-[#40513f]"
                  key={question}
                  onClick={() => {
                    openPetChat();
                    selectPetChatQuestion(question);
                  }}
                  type="button"
                >
                  {question}
                </button>
              ))}
            </div>
            <button
              className="pet-log-pressable mt-4 inline-flex h-11 w-full items-center justify-center gap-2 rounded-2xl bg-[#1f2922] px-4 text-sm font-black text-white shadow-[0_10px_24px_rgba(31,41,34,0.18)]"
              onClick={openPetChat}
              type="button"
            >
              <PetIcon className="h-5 w-5" name="heart" />
              {profile.name}와 대화하기
            </button>
          </div>
        </Card>

        {settings.aiInsightEnabled ? (
          <Card className="bg-gradient-to-br from-white to-[#edf8ed]" motion="rise">
            <div className="flex gap-3">
              <AiMascot active />
              <div className="min-w-0 flex-1">
                <p className="inline-flex items-center gap-1.5 text-sm font-bold text-[#16804b]">
                  <PetIcon className="h-4 w-4" name="sparkle" />
                  AI 질문
                </p>
                <h2 className="mt-1 text-lg font-bold leading-7 text-[#1f2922]">오늘 배변 상태는 어땠나요?</h2>
                <p className="mt-2 text-sm leading-6 text-[#62705f]">어제 기록이 비어 있어 변화 판단에 필요합니다.</p>
                <Link
                  className="pet-log-pressable mt-4 inline-flex h-10 items-center rounded-xl bg-[#16804b] px-5 text-sm font-bold text-white"
                  href="/record"
                >
                  기록하기
                </Link>
              </div>
            </div>
          </Card>
        ) : null}

        <section>
          <SectionHeader
            action={
              <Link className="inline-flex h-8 items-center rounded-full px-2 text-xs font-bold text-[#16804b]" href="/notifications">
                전체 보기
              </Link>
            }
            title="오늘 알림"
          />
          <div className="space-y-3">
            {homeNotifications.map((notification) => (
              <Card
                className={`p-4 ${homeNotificationBorderClasses[notification.tone] ?? `border-l-4 ${toneCard[notification.tone]}`}`}
                key={notification.id}
                motion="rise"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className={`text-xs font-bold ${toneText[notification.tone]}`}>
                      {notification.category} · {notification.dueLabel}
                    </p>
                    <h3 className="mt-1 text-sm font-bold text-[#1f2922]">{notification.title}</h3>
                    <p className="mt-1 text-xs leading-5 text-[#667262]">{notification.detail}</p>
                  </div>
                  <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${toneDot[notification.tone]} ${notification.tone === "red" || notification.tone === "orange" ? "pet-log-pulse-dot" : ""}`} />
                </div>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <SectionHeader title="오늘 요약" />
          <div className="grid grid-cols-3 gap-2">
            {todaySummary.map((item) => (
              <Card className={`p-3 text-center ${toneCard[item.tone]}`} key={item.category} motion="rise">
                <PetIcon className={`mx-auto mb-1 h-4 w-4 ${toneText[item.tone]}`} name={item.category} />
                <p className="text-xs font-bold text-[#788276]">{item.label}</p>
                <p className="mt-2 truncate text-sm font-black text-[#1f2922]">{item.value}</p>
                <p className={`mt-1 text-[11px] font-semibold ${toneText[item.tone]}`}>{item.state}</p>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <SectionHeader title="최근 변화" />
          <Card className={`border-l-4 p-4 ${toneCard[recentChange.tone]}`} motion="rise">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className={`text-xs font-bold ${toneText[recentChange.tone]} flex items-center gap-1.5`}>
                  {recentChange.label}
                  {isAnalysisLoading && <span className="pet-log-pulse-dot h-1.5 w-1.5 bg-current opacity-60" />}
                </p>
                <h3 className="mt-1 text-sm font-black text-[#1f2922]">{recentChange.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[#62705f]">{recentChange.detail}</p>
              </div>
              <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${toneDot[recentChange.tone]} ${recentChange.tone === "red" || recentChange.tone === "orange" ? "pet-log-pulse-dot" : ""}`} />
            </div>
          </Card>
        </section>

        {settings.aiInsightEnabled ? (
          <section>
            <SectionHeader
              action={
                <Link className="inline-flex h-8 items-center rounded-full px-2 text-xs font-bold text-[#16804b]" href="/suggestions">
                  더보기
                </Link>
              }
              title="AI 제안"
            />
            <div className="space-y-3">
              {isAnalysisLoading && homeSuggestions.length === 0 && (
                <Card className="flex items-center justify-center py-8" motion="rise">
                  <div className="flex flex-col items-center gap-2">
                    <span className="pet-log-pulse-dot h-2 w-2 bg-[#16804b]" />
                    <p className="text-xs font-bold text-[#16804b]">AI가 최근 기록을 분석하고 있어요</p>
                  </div>
                </Card>
              )}
              {homeSuggestions.map((suggestion) => (
                <Card className="p-4" key={suggestion.id} motion="rise">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-bold text-[#16804b]">{suggestion.category}</p>
                      <h3 className="mt-1 font-bold text-[#1f2922]">{suggestion.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-[#62705f]">{suggestion.detail}</p>
                    </div>
                    <PetIcon className="mt-0.5 h-5 w-5 shrink-0 text-[#16804b]" name="sparkle" />
                  </div>
                </Card>
              ))}
            </div>
          </section>
        ) : null}

        <section>
          <SectionHeader title="오늘 할 일" />
          <Card motion="rise">
            <p className="text-center text-sm text-[#7b8576]">오늘 할 일이 없습니다.</p>
          </Card>
        </section>

        <section>
          <SectionHeader
            action={
              <Link className="inline-flex h-8 items-center rounded-full px-2 text-xs font-bold text-[#16804b]" href="/timeline">
                전체 보기
              </Link>
            }
            title="최근 기록"
          />
          <div className="space-y-3">
            {latestRecords.length > 0 ? (
              latestRecords.map((record) => (
                <Card className="p-4" key={record.id} motion="rise">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <CategoryBadge category={record.category} />
                        <span className="text-xs font-semibold text-[#8a9286]">{record.time}</span>
                      </div>
                      <p className="mt-2 truncate text-sm font-bold text-[#1f2922]">{record.title}</p>
                      <p className={`mt-1 text-xs font-bold ${toneText[getRecordStatusLabel(record).tone]}`}>
                        {getRecordStatusLabel(record).label}
                      </p>
                    </div>
                    <span className="text-[#9ba597]">›</span>
                  </div>
                </Card>
              ))
            ) : (
                <Card className="p-4" motion="rise">
                <p className="text-sm font-bold text-[#1f2922]">아직 최근 기록이 없습니다.</p>
                <p className="mt-1 text-sm leading-6 text-[#667262]">첫 기록을 저장하면 여기에 바로 표시됩니다.</p>
              </Card>
            )}
          </div>
        </section>
      </div>

      {isPetChatOpen ? (
        <div
          className={`absolute inset-0 z-40 overflow-hidden bg-[#1f2922]/45 backdrop-blur-[1px] ${
            closingPanel === "pet" ? "pet-log-backdrop-out" : "pet-log-backdrop-in"
          }`}
          onClick={closePetChat}
        >
          <section
            aria-label="펫과 대화"
            aria-modal="true"
            className={`absolute bottom-0 right-0 top-0 flex w-full flex-col border-l border-[#dce8d4] bg-[#fffdf7] px-5 pb-5 pt-5 shadow-[-18px_0_48px_rgba(31,41,34,0.2)] ${
              closingPanel === "pet" ? "pet-log-panel-out-right" : "pet-log-panel-in-right"
            }`}
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="shrink-0 border-b border-[#e5eadf] bg-[#fffdf7] pb-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 items-start gap-3">
                  <div className="grid h-12 w-12 shrink-0 place-items-center overflow-hidden rounded-2xl bg-white text-lg font-black text-[#16804b] shadow-inner">
                    {profile.photoDataUrl ? (
                      <Image
                        alt={`${profile.name} 프로필 사진`}
                        className="h-full w-full object-cover"
                        height={48}
                        src={profile.photoDataUrl}
                        unoptimized
                        width={48}
                      />
                    ) : (
                      profile.name.slice(0, 1)
                    )}
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-xl font-black text-[#1f2922]">{profile.name}와 대화</h2>
                    <p className="mt-1 text-sm font-semibold leading-6 text-[#667262]">기록을 바탕으로 일상 대화를 나눠요</p>
                  </div>
                </div>
                <button
                  aria-label="펫 대화 닫기"
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#f0f3ed] text-[#5e6859]"
                  onClick={closePetChat}
                  type="button"
                >
                  <PetIcon className="h-4 w-4" name="close" />
                </button>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto pb-3 pt-4" ref={petChatScrollRef}>
              <div className="space-y-2">
                {petChatQuestions.map((question) => (
                  <button
                    className="flex h-12 w-full items-center gap-3 rounded-full border border-[#dfe6d9] bg-white px-4 text-left text-sm font-bold text-[#40513f] shadow-[0_4px_14px_rgba(49,65,44,0.04)]"
                    key={question}
                    onClick={() => selectPetChatQuestion(question)}
                    type="button"
                  >
                    <PetIcon className="h-5 w-5 shrink-0 text-[#16804b]" name="heart" />
                    <span className="min-w-0 truncate">{question}</span>
                  </button>
                ))}
              </div>

              <div className="mt-4 space-y-2" aria-label="펫 대화 내용">
                <div className="mr-auto max-w-[92%] rounded-2xl border border-[#dfe8d9] bg-white px-4 py-3 text-sm font-semibold leading-6 text-[#334032] shadow-sm">
                  <p className="break-words">나한테 말 걸어줘서 좋아. 오늘 있었던 일도 같이 얘기해보자.</p>
                </div>
                {petChatMessages.map((message) => (
                  <div
                    className={`max-w-[92%] rounded-2xl px-4 py-3 text-sm font-semibold leading-6 shadow-sm ${
                      message.role === "user"
                        ? "ml-auto bg-[#1f2922] text-white"
                        : "mr-auto border border-[#dfe8d9] bg-white text-[#334032]"
                    }`}
                    key={message.id}
                  >
                    <p className="break-words">{message.content}</p>
                  </div>
                ))}
              </div>

              {petChatNotice ? (
                <p className="mt-4 rounded-2xl bg-[#edf8ed] px-4 py-3 text-xs font-bold leading-5 text-[#16804b]">{petChatNotice}</p>
              ) : null}

              <p className="mt-4 rounded-2xl bg-[#f4f7f0] px-4 py-3 text-[11px] font-bold leading-5 text-[#667262]">
                {profile.name}처럼 말하지만 진단은 아니에요. 아픈 상태가 반복되면 AI 질문이나 병원 상담으로 확인해주세요.
              </p>
            </div>

            <div className="flex shrink-0 items-center gap-2 rounded-full border border-[#dfe6d9] bg-white px-4 py-2 shadow-sm">
              <input
                className="h-10 min-w-0 flex-1 bg-transparent text-sm font-semibold text-[#263022] outline-none placeholder:text-[#9aa494]"
                onChange={(event) => {
                  setPetChatInput(event.target.value);
                  if (petChatNotice) {
                    setPetChatNotice("");
                  }
                }}
                placeholder={`${profile.name}에게 말 걸기`}
                value={petChatInput}
              />
              <button
                aria-label={isPetVoiceListening ? "펫 대화 음성 입력 듣는 중" : "펫 대화 음성 입력 시작"}
                className={`grid h-10 w-10 shrink-0 place-items-center rounded-full border ${
                  isPetVoiceListening
                    ? "border-[#16804b] bg-[#e7f4eb] text-[#16804b]"
                    : "border-[#d8e2d2] bg-[#f6f8f3] text-[#667262] disabled:text-[#a9b2a5]"
                }`}
                disabled={isPetVoiceListening}
                onClick={startPetChatVoiceInput}
                title="음성 입력"
                type="button"
              >
                <PetIcon className="h-5 w-5" name="mic" />
              </button>
              <button
                aria-label="펫 대화 보내기"
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#1f2922] text-white"
                onClick={submitPetChatQuestion}
                type="button"
              >
                <PetIcon className="h-5 w-5" name="send" />
              </button>
            </div>
          </section>
        </div>
      ) : null}

      {isChatbotOpen ? (
        <div
          className={`absolute inset-0 z-40 overflow-hidden bg-[#1f2922]/45 backdrop-blur-[1px] ${
            closingPanel === "chatbot" ? "pet-log-backdrop-out" : "pet-log-backdrop-in"
          }`}
          onClick={closeChatbot}
        >
          <section
            aria-label="AI에게 물어보기"
            aria-modal="true"
            className={`absolute bottom-0 left-0 top-0 flex w-full flex-col border-r border-[#dce8d4] bg-white px-5 pb-5 pt-5 shadow-[18px_0_48px_rgba(31,41,34,0.2)] ${
              closingPanel === "chatbot" ? "pet-log-panel-out-left" : "pet-log-panel-in-left"
            }`}
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="shrink-0 border-b border-[#e5eadf] bg-white pb-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-black text-[#1f2922]">AI에게 물어보기</h2>
                  <p className="mt-2 text-sm font-semibold leading-6 text-[#667262]">
                    {profile.name}의 기록을 참고해서 답변해드려요
                  </p>
                </div>
                <button
                  aria-label="물어보기 닫기"
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#f0f3ed] text-[#5e6859]"
                  onClick={closeChatbot}
                  type="button"
                >
                  <PetIcon className="h-4 w-4" name="close" />
                </button>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto pb-3 pt-4" ref={chatbotScrollRef}>
              <div className="space-y-2">
                {chatbotQuestions.map((question) => (
                  <button
                    className="flex h-12 w-full items-center gap-3 rounded-full border border-[#dfe6d9] bg-[#fbfdf8] px-4 text-left text-sm font-bold text-[#40513f] shadow-[0_4px_14px_rgba(49,65,44,0.04)]"
                    disabled={isChatbotSending}
                    key={question.text}
                    onClick={() => selectChatbotQuestion(question.text)}
                    type="button"
                  >
                    <PetIcon className="h-5 w-5 shrink-0 text-[#16804b]" name={question.icon} />
                    <span className="min-w-0 truncate">{question.text}</span>
                  </button>
                ))}
              </div>

              {isChatbotHistoryLoading ? (
                <p className="mt-4 rounded-2xl bg-[#f4f7f0] px-4 py-3 text-xs font-bold leading-5 text-[#667262]">최근 대화를 불러오는 중입니다.</p>
              ) : null}

              {chatbotThread && chatbotThread.messages.length > 0 ? (
                <div className="mt-4 space-y-2" aria-label="최근 대화">
                  {chatbotThread.messages.slice(-8).map((message) => (
                    <div
                      className={`max-w-[92%] rounded-2xl px-4 py-3 text-sm font-semibold leading-6 shadow-sm ${
                        message.role === "user"
                          ? "ml-auto bg-[#16804b] text-white"
                          : "mr-auto border border-[#dfe8d9] bg-[#fbfdf8] text-[#334032]"
                      }`}
                      key={message.id}
                    >
                      <p className="break-words">{message.content}</p>
                      {message.role === "assistant" && message.safetyNotice ? (
                        <p className="mt-2 border-t border-[#dfe8d9] pt-2 text-[11px] font-bold leading-5 text-[#667262]">{message.safetyNotice}</p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}

              {chatbotNotice ? (
                <p className="mt-4 rounded-2xl bg-[#edf8ed] px-4 py-3 text-xs font-bold leading-5 text-[#16804b]">{chatbotNotice}</p>
              ) : null}
            </div>

            <div className="flex shrink-0 items-center gap-2 rounded-full border border-[#dfe6d9] bg-white px-4 py-2 shadow-sm">
              <input
                className="h-10 min-w-0 flex-1 bg-transparent text-sm font-semibold text-[#263022] outline-none placeholder:text-[#9aa494]"
                onChange={(event) => {
                  setChatbotQuestion(event.target.value);
                  if (chatbotNotice) {
                    setChatbotNotice("");
                  }
                }}
                placeholder={`${profile.name}에 대해 궁금한 걸 물어보세요`}
                value={chatbotQuestion}
              />
              <button
                aria-label={isVoiceListening ? "음성 입력 듣는 중" : "음성 입력 시작"}
                className={`grid h-10 w-10 shrink-0 place-items-center rounded-full border ${
                  isVoiceListening
                    ? "border-[#16804b] bg-[#e7f4eb] text-[#16804b]"
                    : "border-[#d8e2d2] bg-[#f6f8f3] text-[#667262] disabled:text-[#a9b2a5]"
                }`}
                disabled={isChatbotSending || isVoiceListening}
                onClick={startChatbotVoiceInput}
                title="음성 입력"
                type="button"
              >
                <PetIcon className="h-5 w-5" name="mic" />
              </button>
              <button
                aria-label="질문 보내기"
                className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[#16804b] text-white disabled:bg-[#8ab99f]"
                disabled={isChatbotSending}
                onClick={submitChatbotQuestion}
                type="button"
              >
                <PetIcon className="h-5 w-5" name="send" />
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}

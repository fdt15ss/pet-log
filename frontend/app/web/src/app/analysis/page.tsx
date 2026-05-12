"use client";

import { useMemo, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { PetIcon } from "@/components/pet-icons";
import { usePetLog } from "@/components/pet-log-provider";
import { Card, MultiLineChart, Pill, SectionHeader } from "@/components/ui";
import {
  getAnalysisHighlights,
  getAnalysisMetrics,
  getAnalysisReport,
  getAnalysisTrendChart,
  getRiskRecords,
  getVetBrief,
  type AnalysisMetricFilter,
  type AnalysisRange,
  type AnalysisTone,
} from "@/lib/analysis-summary";

const reportRanges: { label: string; value: AnalysisRange }[] = [
  { label: "주간 리포트", value: "weekly" },
  { label: "월간 리포트", value: "monthly" },
];

const toneText: Record<AnalysisTone, string> = {
  green: "text-[#16804b]",
  orange: "text-[#bb721e]",
  red: "text-[#be4c3c]",
  blue: "text-[#356aa8]",
};

const toneCard: Record<AnalysisTone, string> = {
  green: "border-[#d8ead1] bg-[#fbfff8]",
  orange: "border-[#f1d9af] bg-[#fffaf0]",
  red: "border-[#f0cbc5] bg-[#fff7f5]",
  blue: "border-[#d4e0f5] bg-[#f6f9ff]",
};

const toneIcon: Record<AnalysisTone, "check" | "alert" | "activity" | "sparkle"> = {
  green: "check",
  orange: "alert",
  red: "alert",
  blue: "activity",
};

const highlightIcon = {
  meal: "meal",
  walk: "walk",
  behavior: "behavior",
} as const;

export default function AnalysisPage() {
  const { records, settings, insights, isAnalysisLoading } = usePetLog();
  const [activeRange, setActiveRange] = useState<AnalysisRange>("weekly");
  const [activeMetric, setActiveMetric] = useState<AnalysisMetricFilter>("all");

  const summary = useMemo(() => getAnalysisReport(records, activeRange), [activeRange, records]);
  const highlights = useMemo(() => getAnalysisHighlights(records, activeRange), [activeRange, records]);
  const riskRecords = useMemo(() => getRiskRecords(records, activeRange), [activeRange, records]);
  
  const aiInsights = useMemo(() => {
    if (!settings.aiInsightEnabled) return [];
    return insights.map((insight, idx) => ({
      id: `insight-${idx}`,
      title: insight.title,
      detail: insight.reason,
      tone: (insight.severity === "alert" ? "red" : insight.severity === "notice" ? "orange" : "green") as "red" | "orange" | "green"
    }));
  }, [insights, settings.aiInsightEnabled]);

  const metrics = useMemo(() => getAnalysisMetrics(records), [records]);
  const vetBrief = useMemo(() => getVetBrief(records), [records]);
  const trendChart = useMemo(() => getAnalysisTrendChart(metrics, activeMetric), [activeMetric, metrics]);
  const scopedRecords = activeRange === "weekly" ? records.slice(0, 7) : records.slice(0, 30);
  const alertCount = scopedRecords.filter((record) => record.status === "alert").length;

  return (
    <AppShell subtitle="데이터를 분석하고 해석해요" title="분석 리포트">
      <div className="space-y-5">
        <div className="grid grid-cols-2 gap-2">
          {reportRanges.map((range) => (
            <Pill active={activeRange === range.value} className="w-full" key={range.value} onClick={() => setActiveRange(range.value)}>
              {range.label}
            </Pill>
          ))}
        </div>

        <Card className="bg-gradient-to-br from-white to-[#f2f8ec]" motion="rise">
          <p className="inline-flex items-center gap-1.5 text-sm font-bold text-[#16804b]">
            <PetIcon className="h-4 w-4" name="sparkle" />
            {summary.period}
          </p>
          <h2 className="mt-2 text-lg font-black text-[#1f2922]">{summary.title}</h2>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <PetIcon className="mx-auto h-4 w-4 text-[#16804b]" name="record" />
              <p className="text-[11px] font-bold text-[#778174]">기록</p>
              <p className="mt-1 text-base font-black text-[#1f2922]">{scopedRecords.length}</p>
            </div>
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <PetIcon className={`mx-auto h-4 w-4 ${alertCount > 0 ? "pet-log-pulse-dot text-[#be4c3c]" : "text-[#16804b]"}`} name={alertCount > 0 ? "alert" : "check"} />
              <p className="text-[11px] font-bold text-[#778174]">주의</p>
              <p className="mt-1 text-base font-black text-[#1f2922]">{alertCount}</p>
            </div>
            <div className="rounded-2xl bg-white/80 px-3 py-3 text-center">
              <PetIcon className="mx-auto h-4 w-4 text-[#356aa8]" name="analysis" />
              <p className="text-[11px] font-bold text-[#778174]">지표</p>
              <p className="mt-1 text-base font-black text-[#1f2922]">{metrics.length}</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {summary.cards.map((card) => (
              <div className={`pet-log-card-rise rounded-2xl border p-3 ${toneCard[card.tone]}`} key={card.id}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-bold text-[#7b8576]">{card.label}</p>
                  <PetIcon className={`h-4 w-4 ${toneText[card.tone]}`} name={toneIcon[card.tone]} />
                </div>
                <p className="mt-1 text-sm font-black text-[#1f2922]">{card.value}</p>
                <p className={`mt-1 text-xs font-bold ${toneText[card.tone]}`}>{card.trend}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-[#596554]">{summary.insight}</p>
        </Card>

        <section>
          <SectionHeader title="핵심 패턴" />
          <div className="grid grid-cols-1 gap-3">
            {highlights.map((highlight) => (
              <Card className={`p-3 ${toneCard[highlight.tone]}`} key={highlight.id} motion="rise">
                <div className="flex items-start gap-3">
                  <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white ${toneText[highlight.tone]}`}>
                    <PetIcon className="h-5 w-5" name={highlightIcon[highlight.id]} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-[#7b8576]">{highlight.label}</p>
                    <h3 className="mt-1 text-sm font-black text-[#1f2922]">{highlight.title}</h3>
                    <p className="mt-1 text-xs font-semibold leading-5 text-[#667262]">{highlight.detail}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <SectionHeader title="이상 징후 기록" />
          <div className="space-y-3">
            {riskRecords.map((record) => (
              <Card className={`p-3 ${toneCard[record.tone]}`} key={record.id} motion="rise">
                <div className="flex items-start gap-3">
                  <PetIcon className={`mt-0.5 h-5 w-5 shrink-0 ${toneText[record.tone]}`} name={toneIcon[record.tone]} />
                  <div className="min-w-0">
                    <p className={`text-xs font-bold ${toneText[record.tone]}`}>{record.meta}</p>
                    <h3 className="mt-1 text-sm font-black text-[#1f2922]">{record.title}</h3>
                    <p className="mt-1 text-xs font-semibold leading-5 text-[#667262]">{record.detail}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <SectionHeader title="변화 추이" />
          <div className="mb-3 grid grid-cols-2 gap-2">
            <Pill active={activeMetric === "all"} className="col-span-2 w-full px-2 text-xs" onClick={() => setActiveMetric("all")}>
              전체
            </Pill>
            {metrics.map((metric) => (
              <Pill active={activeMetric === metric.id} className="w-full px-2 text-xs" key={metric.id} onClick={() => setActiveMetric(metric.id)}>
                {metric.label}
              </Pill>
            ))}
          </div>
          <Card motion="rise">
            <div className="mb-3 flex items-start justify-between gap-3">
              <div>
                <h3 className="inline-flex items-center gap-1.5 font-bold text-[#1f2922]">
                  <PetIcon className={`h-4 w-4 ${toneText[trendChart.tone]}`} name={toneIcon[trendChart.tone]} />
                  {trendChart.title}
                </h3>
                <p className="mt-1 text-xs font-semibold text-[#7b8576]">{trendChart.detail}</p>
              </div>
              <span className={`rounded-full bg-[#f4f7f0] px-3 py-1 text-xs font-bold ${toneText[trendChart.tone]}`}>
                {trendChart.unit}
              </span>
            </div>
            <div className="mb-2 flex flex-wrap gap-3">
              {trendChart.series.map((series) => (
                <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#667262]" key={series.id}>
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: series.color }} />
                  {series.label}
                </span>
              ))}
            </div>
            <MultiLineChart series={trendChart.series} />
          </Card>
        </section>

        <section>
          <SectionHeader title="AI 분석 결과" />
          <div className="space-y-3">
            {isAnalysisLoading && aiInsights.length === 0 && (
              <Card className="flex items-center justify-center py-12" motion="rise">
                <div className="flex flex-col items-center gap-3">
                  <span className="pet-log-pulse-dot h-3 w-3 bg-[#16804b]" />
                  <p className="text-sm font-bold text-[#16804b]">AI가 최근 기록을 심층 분석하고 있어요</p>
                </div>
              </Card>
            )}
            {settings.aiInsightEnabled ? (
              aiInsights.map((insight) => (
                <Card key={insight.id} motion="rise">
                  <p
                    className={`inline-flex items-center gap-1.5 text-sm font-bold ${
                      insight.tone === "red" ? "text-[#be4c3c]" : insight.tone === "orange" ? "text-[#bb721e]" : "text-[#16804b]"
                    }`}
                  >
                    <PetIcon className="h-4 w-4" name={insight.tone === "red" || insight.tone === "orange" ? "alert" : "check"} />
                    {insight.tone === "red" ? "주의" : insight.tone === "orange" ? "확인 필요" : "안정"}
                  </p>
                  <h2 className="mt-2 text-base font-black text-[#1f2922]">{insight.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-[#667262]">{insight.detail}</p>
                </Card>
              ))
            ) : (
              <Card className="p-5 text-center" motion="rise">
                <h2 className="text-sm font-bold text-[#1f2922]">AI 분석이 꺼져 있습니다.</h2>
                <p className="mt-2 text-sm leading-6 text-[#667262]">설정에서 AI 요약과 케어 제안을 다시 켤 수 있습니다.</p>
              </Card>
            )}
          </div>
        </section>

        <section>
          <SectionHeader title="병원 제출용 요약" />
          <Card motion="rise">
            <p className="inline-flex items-center gap-1.5 text-sm font-bold text-[#16804b]">
              <PetIcon className="h-4 w-4" name="medical" />
              {vetBrief.title}
            </p>
            <p className="mt-2 text-sm leading-6 text-[#667262]">{vetBrief.detail}</p>
            <ul className="mt-4 space-y-2">
              {vetBrief.items.map((item) => (
                <li className="rounded-xl bg-[#f4f7f0] px-3 py-2 text-xs font-semibold leading-5 text-[#3d4639]" key={item}>
                  {item}
                </li>
              ))}
            </ul>
          </Card>
        </section>

        <Card className="bg-[#fffaf0]" motion="rise">
          <p className="inline-flex items-center gap-1.5 text-sm font-bold text-[#b56d19]">
            <PetIcon className="h-4 w-4" name="alert" />
            안전 안내
          </p>
          <p className="mt-2 text-sm leading-6 text-[#65533a]">
            AI 분석은 저장된 기록을 바탕으로 한 참고 정보입니다. 확정 진단이 아니며, 증상이 지속되거나 심하면 병원 상담을 권장합니다.
          </p>
        </Card>
      </div>
    </AppShell>
  );
}

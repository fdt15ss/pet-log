import { strict as assert } from "node:assert";
import { getAnalysisMetrics, getAnalysisReport, getAnalysisTrendChart, getVetBrief, getVisibleAnalysisMetrics } from "./analysis-summary";
import type { RecordEntry } from "./types";

const records: RecordEntry[] = [
  {
    id: "behavior-alert",
    date: "4월 29일",
    time: "20:10",
    category: "behavior",
    title: "현관 앞에서 낑낑거림",
    detail: "외출 준비를 보자 낑낑거림이 10분 정도 이어졌어요.",
    status: "alert",
  },
  {
    id: "meal-notice",
    date: "4월 29일",
    time: "08:30",
    category: "meal",
    title: "아침 사료 40g",
    detail: "평소보다 조금 적게 먹었어요.",
    status: "notice",
  },
  {
    id: "walk-normal",
    date: "4월 28일",
    time: "17:00",
    category: "walk",
    title: "산책 20분",
    detail: "컨디션은 안정적이었어요.",
    status: "normal",
  },
];

const report = getAnalysisReport(records, "weekly");
assert.equal(report.cards.length, 4);
assert.equal(report.cards.find((card) => card.id === "behavior")?.tone, "red");
assert.ok(report.insight.includes("주의"));

const emptyReport = getAnalysisReport([], "monthly");
assert.ok(emptyReport.insight.includes("기록"));

const metrics = getAnalysisMetrics(records);
assert.equal(metrics.find((metric) => metric.id === "behavior")?.values.at(-1), 1);
assert.equal(metrics.find((metric) => metric.id === "stool")?.trend, "최근 기록 없음");

const visibleAllMetrics = getVisibleAnalysisMetrics(metrics, "all");
assert.deepEqual(
  visibleAllMetrics.map((metric) => metric.id),
  ["meal", "walk", "stool", "behavior"],
);

const visibleBehaviorMetrics = getVisibleAnalysisMetrics(metrics, "behavior");
assert.deepEqual(
  visibleBehaviorMetrics.map((metric) => metric.id),
  ["behavior"],
);

const allTrendChart = getAnalysisTrendChart(metrics, "all");
assert.equal(allTrendChart.title, "전체 변화");
assert.deepEqual(
  allTrendChart.series.map((series) => series.id),
  ["meal", "walk", "stool", "behavior"],
);

const behaviorTrendChart = getAnalysisTrendChart(metrics, "behavior");
assert.equal(behaviorTrendChart.title, "행동");
assert.deepEqual(
  behaviorTrendChart.series.map((series) => series.id),
  ["behavior"],
);

const vetBrief = getVetBrief(records);
assert.equal(vetBrief.items.length, 3);
assert.ok(vetBrief.detail.includes("병원 상담"));

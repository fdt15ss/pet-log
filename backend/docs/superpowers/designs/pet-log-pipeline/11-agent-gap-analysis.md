# 기획서 재점검 기준 누락 Agent

## 기준

`기획.md`의 핵심 방향은 기록 저장이 아니라 누적 기록을 해석하고 행동 개선으로 연결하는 AI Agent다. 따라서 단순 CRUD나 화면 조립이 아니라 판단, 요약, 질문, 알림, 입력 이해가 필요한 책임을 agent 후보로 본다.

## 현재 반영된 agent

| 기획 요구 | 현재 설계 |
| --- | --- |
| 자연어 기록 입력/자동 구조화 | `RecordStructuringAgent` |
| 누적 데이터 기반 분석, 상태 변화, 기록 누락 | `ContextAnalysisAgent` |
| 이상 징후 감지 | `RiskDetectionAgent` |
| 행동 가이드/개선 방향 제안 | `SuggestionAgent` |
| 일정 기반 관리/리마인더 | `ReminderAgent` |
| 펫과 대화하는 감성 인터페이스 | `PetPersonaAgent` + `PetChatPipeline` |
| 보호자 AI 케어 질문 | `CareQuestionPipeline` + `CareAnswerProviderInterface` |

## 누락 agent 후보

| 우선순위 | 후보 | 기획 근거 | 필요한 이유 |
| --- | --- | --- | --- |
| 1 | `RecordSummaryAgent` | 문제 행동 요약, 주간/월간 리포트, 병원 제출용 요약, 변화 기록 정리 | `ContextAnalysisAgent`는 insight를 만들지만 사람이 읽을 문장형 요약/리포트를 만들지 않는다. |
| 2 | `ProactiveQuestionAgent` | 홈의 AI가 먼저 질문하는 한줄 구간, 기록 누락/최근 변화 확인 | 홈 composer가 문구를 조립하는 것과 "무엇을 먼저 물을지" 판단하는 책임은 분리해야 한다. |
| 3 | `NotificationAgent` | 이상 징후 알림, 행동 변화 알림, 일정 알림, 기록 누락 알림 | 알림 후보 생성은 push 전송과 다르며, dedupe와 안전 문구 정책이 필요하다. |
| 4 | `PhotoRecordUnderstandingAgent` | 사진 첨부 기록, 사진 인식 아이디어 | 사진에서 관찰 가능한 정보를 구조화하고 낮은 확신은 보호자 확인으로 돌리는 입력 이해 책임이 필요하다. |

## 범위 밖 또는 후순위

| 후보 | 판단 |
| --- | --- |
| `CommunityRecommendationAgent` | 커뮤니티 카테고리/글 추천은 care core 밖의 별도 bounded context로 둔다. |
| `CommerceRecommendationAgent` | 사료/용품/제휴 추천은 비즈니스 모델 단계에서 분리 설계한다. |
| `LocationRecommendationAgent` | 산책 스팟, 동반 업소, 병원 지도 추천은 위치 권한과 외부 API 설계 이후 다룬다. |
| `GoalMissionAgent` | 다이어트/문제행동 미션은 제안 agent가 안정화된 뒤 gamification context로 분리한다. |
| `ExpenseUnderstandingAgent` | 영수증/가계부는 현재 care pipeline과 직접 관련이 낮아 후순위다. |

## 추천 반영 순서

1. `RecordSummaryAgent` 계약을 먼저 고정한다.
2. 홈 경험에 직접 노출되는 `ProactiveQuestionAgent` 계약을 추가한다.
3. `NotificationAgent`로 알림 후보 생성과 전송 책임을 분리한다.
4. 입력 채널 확장 단계에서 `PhotoRecordUnderstandingAgent`를 추가한다.

## 결정

- 누락 agent 후보는 모두 application interface부터 정의한다.
- 실제 LLM, vision, push provider는 infrastructure 뒤에 둔다.
- 의료 판단 단정 표현은 모든 agent에서 금지한다.
- 커뮤니티, 커머스, 위치 추천은 core care agent 설계에 섞지 않는다.

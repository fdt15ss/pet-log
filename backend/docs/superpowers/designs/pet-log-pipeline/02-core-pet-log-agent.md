# Core Pet Log Agent

## 책임

`PetLogAgentPipeline`은 제품-facing core orchestration boundary다. 기록 입력을 받아 구조화, 맥락 분석, 위험 감지, 제안, 리마인더까지 연결한다.

```text
PetLogAgentInput
  -> RecordStructuringAgent
  -> ContextAnalysisAgent
  -> RiskDetectionAgent
  -> RecordRepositoryInterface
  -> SuggestionAgent
  -> ReminderAgent
  -> PetLogAgentResult
```

## 내부 Agent

### RecordStructuringAgent

자연어, 음성 변환 텍스트, 빠른 입력을 structured record candidate로 바꾼다.

```text
PetLogAgentInput
  -> RecordStructurerInterface
  -> StructuredRecordCandidate
```

### ContextAnalysisAgent

누적 기록, 일정, 프로필, 설정을 읽어 상태 변화와 기록 누락을 감지한다.

```text
PetProfile + recent records + due schedules
  -> PatternAnalyzerInterface
  -> MissingRecordPolicyInterface
  -> ContextAnalysisResult
```

### RecordSummaryAgent 후보

`기획.md`는 누적 기록 기반으로 문제 행동 요약, 주간/월간 리포트, 변화 기록 정리, 병원 제출용 요약을 요구한다. 현재 `ContextAnalysisAgent`는 패턴과 누락 insight를 만들지만, 여러 기존 기록을 보호자나 병원에 보여줄 문장형 요약으로 정리하는 전용 agent는 아직 없다.

후속 구현 후보:

```text
PetProfile + records + context insights + due schedules
  -> RecordSummaryProviderInterface 또는 RecordSummaryComposerInterface
  -> RecordSummaryResult
```

책임 범위:

- 최근 기록을 시간 흐름 기준으로 묶어 요약한다.
- 반복 행동, 상태 변화, 누락 기록을 사람이 읽을 수 있는 문장으로 정리한다.
- 주간/월간 리포트와 병원 제출용 요약이 재사용할 수 있는 공통 summary를 만든다.
- 의료 판단은 하지 않고 `SafetyNotice`와 병원 상담 안내 정책을 따른다.

### RiskDetectionAgent

현재 입력과 누적 기록에서 위험 신호를 감지한다.

```text
input text + recent records
  -> RiskSignalPolicyInterface
  -> SafetyNotice tuple
```

### SuggestionAgent

context insight와 safety notice를 행동 제안으로 바꾼다.

```text
PetProfile + insights + safety notices
  -> SuggestionComposerInterface
  -> CareSuggestion tuple
```

### ReminderAgent

성장 단계, 예방접종, 약, 검진, 사료 변경 시점 같은 일정 기반 관리 후보를 만든다.

```text
PetProfile + records + due schedules
  -> ReminderPlannerInterface
  -> PlannedReminder tuple
```

## 결정

- 보호자 확인이 필요한 구조화 후보는 저장 전 수정 요청으로 돌린다.
- 저장 이후에 제안과 리마인더를 만든다.
- `ContextAnalysisAgent`는 insight 산출까지 담당하고, 누적 기록을 문장형 리포트로 정리하는 책임은 후속 `RecordSummaryAgent` 계열로 분리한다.
- 의료 판단은 하지 않고 위험 신호 notice만 만든다.

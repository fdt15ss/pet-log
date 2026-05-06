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
- 의료 판단은 하지 않고 위험 신호 notice만 만든다.

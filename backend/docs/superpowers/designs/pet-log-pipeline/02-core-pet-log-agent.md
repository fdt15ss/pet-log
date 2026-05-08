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

자연어, 음성 변환 텍스트, 빠른 입력을 structured record candidate 묶음으로 바꾼다.

```text
PetLogAgentInput
  -> RecordStructurerInterface
  -> StructuredRecordBatch
```

입력 문장 하나에 여러 사건이 섞이면 `StructuredRecordBatch.candidates`에 여러 후보를 담는다. 확인이 끝난 batch는 각 후보를 별도 `PetRecord`로 저장한다.

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

기획서 기준 흐름은 "기록을 저장한다"가 아니라 "기록을 해석하고, 해석 결과를 보호자가 이해할 수 있는 말로 요약하고, 행동 제안으로 연결한다"다. 따라서 요약 기능은 단순 composer가 아니라 모델 호출 provider를 가진 agent 흐름으로 본다.

권장 흐름:

```text
PetRecord tuple
  -> ContextAnalysisAgent
  -> ContextAnalysisResult

PetProfile + records + ContextAnalysisResult + due schedules
  -> RecordSummaryAgent
  -> RecordSummaryProviderInterface
  -> RecordSummaryResult
```

역할 경계:

- `ContextAnalysisAgent`: 누적 기록에서 패턴, 변화, 누락, 위험 맥락을 분석한다.
- `RecordSummaryAgent`: 어떤 기록과 분석 결과를 요약할지 결정하고 provider 호출을 조립한다.
- `RecordSummaryProviderInterface`: GPT, 로컬 모델, LangChain adapter 등 실제 모델 호출을 숨긴다.
- `RecordSummaryComposerInterface`: 모델을 쓰지 않는 규칙 기반 fallback 또는 모델 결과 포맷팅에만 사용한다.
- `RecordSummaryResult`: 홈, 분석 리포트, 병원 제출용 요약에서 재사용할 공통 결과다.

책임 범위:

- 최근 기록을 시간 흐름 기준으로 묶어 요약한다.
- 반복 행동, 상태 변화, 누락 기록을 사람이 읽을 수 있는 문장으로 정리한다.
- 주간/월간 리포트와 병원 제출용 요약이 재사용할 수 있는 공통 summary를 만든다.
- 의료 판단은 하지 않고 `SafetyNotice`와 병원 상담 안내 정책을 따른다.
- 모델이 생성한 문장도 진단이나 확정 표현을 포함하면 안 된다.

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

- 보호자 확인이 필요한 구조화 후보 묶음은 저장 전 수정 요청으로 돌린다.
- 저장 이후에 제안과 리마인더를 만든다.
- `ContextAnalysisAgent`는 insight 산출까지 담당하고, 누적 기록을 문장형 리포트로 정리하는 책임은 후속 `RecordSummaryAgent` 계열로 분리한다.
- 모델 기반 요약은 `RecordSummaryAgent`가 직접 LLM SDK를 호출하지 않고 `RecordSummaryProviderInterface` 뒤로 숨긴다.
- 의료 판단은 하지 않고 위험 신호 notice만 만든다.

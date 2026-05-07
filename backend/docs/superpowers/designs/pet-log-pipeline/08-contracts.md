# Domain, DTO, Interface 계약

## Domain 타입

구현 위치는 `src/domain/models.py`, `src/domain/enums.py`다.

| 타입 | 책임 |
| --- | --- |
| `PetProfile` | 펫 프로필 |
| `PetRecord` | 저장된 기록 |
| `StructuredRecordCandidate` | 저장 전 구조화 후보 |
| `CareInsight` | 맥락 분석 결과 |
| `ContextAnalysisResult` | insight와 기록 누락 분석 묶음 |
| `CareSuggestion` | 보호자 행동 제안 |
| `PlannedReminder` | 일정/리마인더 후보 |
| `SafetyNotice` | 위험 신호 또는 병원 상담 안내 |
| `CareContext` | 케어 질문/펫 대화 공통 context |

## Application DTO

구현 위치는 `src/application/dto.py`다.

| DTO | 책임 |
| --- | --- |
| `PetLogAgentInput` | 자연어 기록 입력 |
| `PetLogAgentResult` | core agent 처리 결과 |
| `HomeFeedResult` | 홈 화면 조립 결과 |
| `CareQuestionResult` | AI 케어 질문 답변 |
| `PetChatResult` | 펫 대화 답변 |
| `HospitalSummaryResult` | 병원 제출용 요약 |
| `RecordSummaryResult` | 누적 기록 기반 정리/리포트 공통 결과 |

## Interface

구현 위치는 `src/application/interfaces/` 패키지다. `src/application/interfaces/__init__.py`가 전체 interface를 다시 export하므로 기존처럼 `from application.interfaces import ...`로 가져올 수 있다. 실제 동작은 `infrastructure`, `agent_runtime`, `tools`에서 구현한다.

### Pipeline interfaces

파일: `src/application/interfaces/pipelines.py`

- `PetLogAgentPipelineInterface`
- `HomeFeedPipelineInterface`
- `CareQuestionPipelineInterface`
- `PetChatPipelineInterface`
- `HospitalSummaryPipelineInterface`

### Agent interfaces

파일: `src/application/interfaces/agents.py`

- `RecordStructuringAgentInterface`
- `ContextAnalysisAgentInterface`
- `RiskDetectionAgentInterface`
- `SuggestionAgentInterface`
- `ReminderAgentInterface`
- `RecordSummaryAgentInterface`
- `CareContextBuilderInterface`
- `PetPersonaAgentInterface`

### Repository and reader interfaces

파일: `src/application/interfaces/repositories.py`

- `PetProfileReaderInterface`
- `RecordHistoryReaderInterface`
- `RecordRepositoryInterface`
- `ScheduleContextReaderInterface`
- `PetLogAgentResultReaderInterface`

### Provider interfaces

파일: `src/application/interfaces/providers.py`

- `RecordStructurerInterface`
- `CareAnswerProviderInterface`
- `PetPersonaResponderInterface`
- `SpeechToTextInterface`
- `TextToSpeechInterface`

### Policy interfaces

파일: `src/application/interfaces/policies.py`

- `PatternAnalyzerInterface`
- `MissingRecordPolicyInterface`
- `RiskSignalPolicyInterface`
- `SuggestionComposerInterface`
- `ReminderPlannerInterface`
- `SafetyGuardInterface`

### Composer interfaces

파일: `src/application/interfaces/composers.py`

- `HomeFeedComposerInterface`
- `RecordSummaryComposerInterface`
- `HospitalReportComposerInterface`

## Record summary 계약 후보

기획서의 `문제 행동 요약`, `최근 변화 정리`, `주간/월간 리포트`, `병원 제출용 요약`은 모두 누적 기록 묶음을 사람이 읽을 수 있는 형태로 정리하는 공통 계약을 필요로 한다.

초기 DTO 후보:

```text
RecordSummaryResult
  summary: str
  record_ids: tuple[str, ...]
  highlights: tuple[str, ...]
  behavior_patterns: tuple[str, ...]
  missing_record_notes: tuple[str, ...]
  safety_notice: SafetyNotice | None
```

초기 agent 계약 후보:

```text
RecordSummaryAgentInterface.summarize(
  pet: PetProfile,
  records: tuple[PetRecord, ...],
  context: ContextAnalysisResult,
  due_items: tuple[PlannedReminder, ...],
) -> RecordSummaryResult
```

구현 방향:

- `ContextAnalysisAgent`가 만든 insight를 재사용한다.
- 시간 흐름 기반 변화와 반복 행동을 문장형으로 정리한다.
- 병원 제출용 문구는 `HospitalReportComposerInterface`에서 목적에 맞게 재구성한다.
- 의료 판단 단정 표현은 금지하고, 위험 신호는 `SafetyNotice`로 분리한다.

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
- `HospitalReportComposerInterface`

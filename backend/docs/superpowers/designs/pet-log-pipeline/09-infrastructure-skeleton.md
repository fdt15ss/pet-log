# Infrastructure Skeleton

현재 구현체는 인터페이스를 상속받는 클래스 뼈대만 둔다. 모든 method body는 `raise NotImplementedError`이며, 실제 DB/AI/rule/runtime 로직은 없다.

## Skeleton 위치

| 파일 | 클래스 | 구현 interface | 현재 상태 |
| --- | --- | --- | --- |
| `src/infrastructure/llm/record_structuring/provider.py` | `RecordStructurer` | `RecordStructurerInterface` | LangChain structured output 구현 |
| `src/infrastructure/llm/care_answer_provider.py` | `CareAnswerProvider` | `CareAnswerProviderInterface` | skeleton |
| `src/infrastructure/llm/pet_persona_responder.py` | `PetPersonaResponder` | `PetPersonaResponderInterface` | skeleton |
| `src/infrastructure/speech/speech_to_text.py` | `SpeechToTextProvider` | `SpeechToTextInterface` | skeleton |
| `src/infrastructure/speech/text_to_speech.py` | `TextToSpeechProvider` | `TextToSpeechInterface` | skeleton |
| `src/infrastructure/policies/pattern_analyzer.py` | `PatternAnalyzer` | `PatternAnalyzerInterface` | skeleton |
| `src/infrastructure/policies/missing_record_policy.py` | `MissingRecordPolicy` | `MissingRecordPolicyInterface` | skeleton |
| `src/infrastructure/policies/risk_signal_policy.py` | `RiskSignalPolicy` | `RiskSignalPolicyInterface` | skeleton |
| `src/infrastructure/policies/suggestion_composer.py` | `SuggestionComposer` | `SuggestionComposerInterface` | skeleton |
| `src/infrastructure/policies/reminder_planner.py` | `ReminderPlanner` | `ReminderPlannerInterface` | skeleton |
| `src/infrastructure/policies/safety_guard.py` | `SafetyGuard` | `SafetyGuardInterface` | skeleton |
| `src/infrastructure/repositories/pet_profile_repository.py` | `PetProfileRepository` | `PetProfileReaderInterface` | skeleton |
| `src/infrastructure/repositories/record_repository.py` | `RecordRepository` | `RecordHistoryReaderInterface`, `RecordRepositoryInterface` | skeleton |
| `src/infrastructure/repositories/schedule_repository.py` | `ScheduleRepository` | `ScheduleContextReaderInterface` | skeleton |
| `src/infrastructure/repositories/pet_log_agent_result_repository.py` | `PetLogAgentResultRepository` | `PetLogAgentResultReaderInterface` | skeleton |
| `src/infrastructure/composers/home_feed_composer.py` | `HomeFeedComposer` | `HomeFeedComposerInterface` | skeleton |
| `src/infrastructure/composers/hospital_report_composer.py` | `HospitalReportComposer` | `HospitalReportComposerInterface` | skeleton |

## 후속 구현 후보

| 후보 | 기준 interface | 목적 |
| --- | --- | --- |
| `MockRecordStructurer` | `RecordStructurerInterface` | 네트워크 없는 구조화 테스트 |
| `InMemoryPetProfileRepository` 또는 `DatabasePetProfileRepository` | `PetProfileReaderInterface` | 테스트/로컬 demo 또는 실제 DB profile 조회 |
| `DatabaseRecordRepository` | `RecordRepositoryInterface`, `RecordHistoryReaderInterface` | 기록 저장/조회 |
| `RuleBased*` policy 구현체 | policy interfaces | 식사/산책/배변/행동 패턴, 위험 신호, 기록 누락, 리마인더 |
| `LLM*` provider 구현체 | LLM interfaces | 케어 질문, 펫 대화, 병원 요약 생성 |
| `Speech*` provider 구현체 | speech interfaces | 음성 입력 STT, 음성 응답 TTS |

## 결정 보류

- 실제 DB row와 domain model 매핑은 repository 구현체 설계 시 확정한다.
- `PetChatPipeline`의 말투 규칙은 프로필의 `personality`, 최근 기록, 안전 규칙을 기반으로 별도 prompt/spec 문서에서 정한다.
- `CareQuestionPipeline`과 `PetChatPipeline`을 같은 LLM provider로 구현하더라도 application interface는 분리한다.
- 실제 AI provider 도입 시 sync/async 전환을 재검토한다. 현재 interface는 단순성을 위해 sync 기준이다.
- 커뮤니티, 쇼핑, 공동 관리의 전체 기능은 core care pipeline 밖으로 두고, 추천/병원/상품 연계가 필요할 때 별도 bounded context로 분리한다.

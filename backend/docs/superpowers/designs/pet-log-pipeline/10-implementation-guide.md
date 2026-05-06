# 구현 가이드

이 문서는 처음 보는 개발자가 펫로그 backend 구조를 빠르게 이해하고, 기능별로 어디를 구현해야 하는지 찾기 위한 안내서다.

## 한 줄 요약

```text
presentation -> application pipeline -> application agents -> interfaces -> infrastructure/tools/agent_runtime
```

- `presentation`은 외부 요청이 들어오는 입구다.
- `application`은 제품 기능 흐름을 조립한다.
- `interfaces`는 application이 필요로 하는 계약이다.
- `infrastructure`는 DB, LLM, rule 같은 실제 구현체다.
- `agent_runtime`, `middleware`, `tools`는 LLM agent 실행을 위한 공통 계층이다.

## 먼저 읽을 파일

| 순서 | 파일 | 이유 |
| --- | --- | --- |
| 1 | `docs/superpowers/designs/pet-log-pipeline-interface-design.md` | 전체 설계 인덱스 |
| 2 | `docs/superpowers/designs/pet-log-pipeline/01-package-structure.md` | 폴더별 책임 |
| 3 | `docs/superpowers/designs/pet-log-pipeline/08-contracts.md` | DTO와 interface 이름 |
| 4 | `src/application/interfaces/` | 구현체가 맞춰야 하는 실제 Protocol |
| 5 | `src/composition.py` | 구현체를 조립할 위치 |

## 폴더별 역할

### `src/domain/`

순수 데이터 타입이 있는 곳이다. FastAPI, DB, OpenAI SDK를 import하지 않는다.

구현 예:
- `PetProfile`
- `PetRecord`
- `StructuredRecordCandidate`
- `CareInsight`
- `CareSuggestion`

수정 기준:
- 새로운 핵심 개념이 생길 때만 수정한다.
- DB row나 API request 모양에 맞추기 위해 domain을 오염시키지 않는다.

### `src/application/dto.py`

pipeline의 입력과 출력 객체가 있는 곳이다.

구현 예:
- `PetLogAgentInput`
- `PetLogAgentResult`
- `HomeFeedResult`
- `CareQuestionResult`
- `PetChatResult`

수정 기준:
- 화면/API/agent 흐름에서 새 입력 또는 결과 필드가 필요할 때 수정한다.

### `src/application/interfaces/`

application이 외부에 기대하는 계약이다. 실제 동작 구현은 없다.

예:
- `pipelines.py`: pipeline 흐름 계약
- `agents.py`: application agent 계약
- `repositories.py`: 저장소/reader 계약
- `providers.py`: LLM/STT/TTS provider 계약
- `policies.py`: rule/policy 계약
- `composers.py`: 화면/리포트 조립 계약

수정 기준:
- agent나 pipeline이 새 능력을 필요로 할 때 먼저 interface를 정의한다.
- 구현체 이름이나 특정 기술 이름을 interface에 넣지 않는다.

### `src/application/agents/`

제품 기능을 맡는 LLM agent 단위다. 각 agent는 직접 DB나 OpenAI SDK를 호출하지 않고 interface만 사용한다.

예:
- `RecordStructuringAgent`
- `ContextAnalysisAgent`
- `RiskDetectionAgent`
- `SuggestionAgent`
- `ReminderAgent`

수정 기준:
- 여러 interface 호출을 어떤 순서로 묶을지 정할 때 수정한다.
- 실제 DB/LLM/rule 로직은 여기 넣지 않는다.

### `src/application/pipelines/`

사용자 기능 흐름을 조립하는 곳이다.

예:
- `PetLogAgentPipeline`: 기록 입력 core 흐름
- `HomeFeedPipeline`: 홈 화면 흐름
- `CareQuestionPipeline`: AI 케어 질문 흐름
- `PetChatPipeline`: 펫 대화 흐름
- `HospitalSummaryPipeline`: 병원 제출 요약 흐름

수정 기준:
- 기능 흐름의 순서가 바뀌거나 새 surface가 생길 때 수정한다.

### `src/infrastructure/`

실제 구현체가 들어가는 곳이다. 대부분의 다음 개발은 여기서 시작한다.

예:
- `infrastructure/llm/`: OpenAI, 로컬 모델, mock LLM provider
- `infrastructure/speech/`: STT/TTS provider
- `infrastructure/repositories/`: DB 또는 in-memory 저장소
- `infrastructure/policies/`: rule-based 분석/추천/위험 감지
- `infrastructure/composers/`: 홈 카드, 병원 리포트 문구 조립

수정 기준:
- 실제 동작을 만들 때 구현한다.
- application interface를 상속하거나 충족해야 한다.

### `src/agent_runtime/`

LLM agent 실행 공통 계층이다.

예:
- prompt 조립
- tool registry
- tool calling loop
- memory hook

수정 기준:
- 단순 rule/mock 구현 단계에서는 건드리지 않아도 된다.
- 실제 tool-calling LLM agent를 붙일 때 구현한다.

### `src/middleware/`

agent 실행 전후 공통 처리다.

예:
- safety
- logging
- tracing
- retry
- validation

수정 기준:
- 여러 agent에 공통으로 적용할 처리만 넣는다.
- 특정 기능 하나만을 위한 로직은 agent나 infrastructure에 둔다.

### `src/tools/`

LLM agent가 호출할 수 있는 기능 묶음이다.

예:
- 기록 조회
- 프로필 조회
- 일정 조회
- 케어 답변 보조 기능
- STT/TTS 보조 기능

수정 기준:
- agent_runtime의 tool calling에서 사용할 기능을 schema-first로 만들 때 구현한다.

### `src/presentation/`

외부 요청이 application으로 들어오는 입구다.

예:
- `presentation/http/`: FastAPI router/controller 후보
- `presentation/cli/`: 로컬 CLI demo 후보

수정 기준:
- HTTP API나 CLI를 붙일 때 구현한다.
- 비즈니스 로직은 넣지 않고 pipeline 호출과 request/response 변환만 둔다.

### `src/composition.py`

구현체를 실제 pipeline에 연결하는 곳이다.

예:

```text
RecordStructurer 구현체 생성
RecordRepository 구현체 생성
RecordStructuringAgent 생성
PetLogAgentPipeline 생성
```

수정 기준:
- interface 구현체를 조립해서 실행 가능한 pipeline을 만들 때 수정한다.

## 기능별 구현 위치

| 만들 기능 | 먼저 볼 interface | 구현 위치 | 연결 위치 |
| --- | --- | --- | --- |
| 자연어 기록 구조화 | `RecordStructurerInterface` | `src/infrastructure/llm/record_structurer.py` | `RecordStructuringAgent` |
| 펫 프로필 조회 | `PetProfileReaderInterface` | `src/infrastructure/repositories/pet_profile_repository.py` | `CareContextBuilder`, pipeline |
| 최근 기록 조회 | `RecordHistoryReaderInterface` | `src/infrastructure/repositories/record_repository.py` | `ContextAnalysisAgent`, `CareContextBuilder` |
| 기록 저장 | `RecordRepositoryInterface` | `src/infrastructure/repositories/record_repository.py` | `PetLogAgentPipeline` |
| 일정 조회 | `ScheduleContextReaderInterface` | `src/infrastructure/repositories/schedule_repository.py` | `CareContextBuilder`, `ReminderAgent` |
| 위험 신호 감지 | `RiskSignalPolicyInterface` | `src/infrastructure/policies/risk_signal_policy.py` | `RiskDetectionAgent` |
| 기록 누락 감지 | `MissingRecordPolicyInterface` | `src/infrastructure/policies/missing_record_policy.py` | `ContextAnalysisAgent` |
| 행동 제안 생성 | `SuggestionComposerInterface` | `src/infrastructure/policies/suggestion_composer.py` | `SuggestionAgent` |
| 리마인더 생성 | `ReminderPlannerInterface` | `src/infrastructure/policies/reminder_planner.py` | `ReminderAgent` |
| AI 케어 답변 | `CareAnswerProviderInterface` | `src/infrastructure/llm/care_answer_provider.py` | `CareQuestionPipeline` |
| 펫 말투 응답 | `PetPersonaResponderInterface` | `src/infrastructure/llm/pet_persona_responder.py` | `PetPersonaAgent` |
| 음성 입력 STT | `SpeechToTextInterface` | `src/infrastructure/speech/speech_to_text.py` | `presentation`, `tools/speech_tools.py` |
| 음성 응답 TTS | `TextToSpeechInterface` | `src/infrastructure/speech/text_to_speech.py` | `presentation`, `tools/speech_tools.py` |
| 홈 화면 카드 조립 | `HomeFeedComposerInterface` | `src/infrastructure/composers/home_feed_composer.py` | `HomeFeedPipeline` |
| 병원 제출 요약 | `HospitalReportComposerInterface` | `src/infrastructure/composers/hospital_report_composer.py` | `HospitalSummaryPipeline` |
| HTTP API | pipeline interfaces | `src/presentation/http/` | `src/composition.py` |
| CLI demo | pipeline interfaces | `src/presentation/cli/` | `src/composition.py` |

## 추천 구현 순서

### 1. In-memory repositories

처음에는 DB 없이 동작을 확인하는 것이 좋다.

구현 위치:
- `src/infrastructure/repositories/pet_profile_repository.py`
- `src/infrastructure/repositories/record_repository.py`
- `src/infrastructure/repositories/schedule_repository.py`

검증 목표:
- 펫 프로필을 조회할 수 있다.
- 최근 기록을 조회할 수 있다.
- 구조화 후보를 기록으로 저장할 수 있다.

### 2. Mock 또는 rule-based `RecordStructurer`

LLM 없이 자연어 입력을 구조화 후보로 바꾸는 최소 구현을 만든다.

구현 위치:
- `src/infrastructure/llm/record_structurer.py`

검증 목표:
- `"오늘 밥을 조금 먹고 산책은 못 했어"` 같은 입력이 `StructuredRecordCandidate`로 변환된다.

### 3. Rule-based policies

분석/위험/제안/리마인더는 처음에는 rule-based로 만든다.

구현 위치:
- `src/infrastructure/policies/pattern_analyzer.py`
- `src/infrastructure/policies/risk_signal_policy.py`
- `src/infrastructure/policies/suggestion_composer.py`
- `src/infrastructure/policies/reminder_planner.py`

검증 목표:
- 반복되는 이상 패턴을 notice로 만들 수 있다.
- 위험 키워드는 safety notice로 만들 수 있다.
- 보호자 행동 제안을 만들 수 있다.

### 4. `composition.py` wiring

각 구현체를 pipeline에 연결한다.

구현 위치:
- `src/composition.py`

검증 목표:
- `build_pet_log_agent_pipeline()`이 실행 가능한 `PetLogAgentPipeline`을 반환한다.

### 5. CLI 또는 HTTP entrypoint

pipeline이 조립된 뒤 외부 입구를 붙인다.

구현 위치:
- CLI: `src/presentation/cli/`
- HTTP: `src/presentation/http/`

검증 목표:
- CLI 또는 HTTP 요청으로 기록 입력을 처리할 수 있다.

### 6. 실제 LLM provider

mock/rule 기반 흐름이 검증된 뒤 실제 LLM을 붙인다.

구현 위치:
- `src/infrastructure/llm/`
- 필요하면 `src/agent_runtime/`
- 필요하면 `src/tools/`

검증 목표:
- LLM provider를 바꿔도 application pipeline은 바뀌지 않는다.

## 구현할 때 지켜야 할 방향

- 새 기능은 먼저 `application/interfaces/`의 계약을 확인한다.
- application layer에서 DB, FastAPI, OpenAI SDK를 직접 import하지 않는다.
- 실제 동작은 `infrastructure` 또는 `agent_runtime/tools`에 둔다.
- pipeline은 흐름을 조립하고, 세부 판단 로직을 과하게 들고 있지 않는다.
- 테스트는 작은 경계부터 시작한다.
- 의료 판단처럼 위험한 문구는 `SafetyNotice`와 병원 상담 안내로 제한한다.

## 빠른 예시

### 자연어 기록 구조화를 구현한다면

1. `RecordStructurerInterface`를 확인한다.
2. `src/infrastructure/llm/record_structurer.py`를 구현한다.
3. `RecordStructuringAgent`가 해당 구현체를 호출하는지 확인한다.
4. `src/composition.py`에서 구현체를 agent에 주입한다.
5. 구조화 입력/출력 테스트를 추가한다.

### DB 저장을 구현한다면

1. `RecordRepositoryInterface`를 확인한다.
2. `src/infrastructure/repositories/record_repository.py`를 구현한다.
3. domain model과 DB row 매핑은 repository 안에 둔다.
4. `PetLogAgentPipeline`에서 저장 흐름이 호출되는지 확인한다.
5. repository 단위 테스트 또는 integration test를 추가한다.

### API를 붙인다면

1. `src/composition.py`에서 pipeline을 만들 수 있게 한다.
2. `src/presentation/http/`에 router/controller를 둔다.
3. HTTP request를 `PetLogAgentInput`으로 변환한다.
4. pipeline 결과를 response DTO로 변환한다.
5. application/domain에 FastAPI import를 추가하지 않는다.

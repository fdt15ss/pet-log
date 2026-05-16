# 에이전트 툴 / 미들웨어 매핑

LangGraph 파이프라인(`LangGraphPetLogAgentPipeline`)은 3개의 노드로 구성된다.  
각 노드에 등록된 툴과 미들웨어는 `agent_runtime/tool_registry.py`의 `build_pet_log_node_wiring()`에서 조립된다.

---

## 노드별 툴 & 미들웨어

### 1. `structure_record` — 기록 구조화

사용자 입력 텍스트를 구조화된 레코드 후보(`StructuredRecordCandidate`)로 변환한다.  
LLM 호출만 하므로 툴은 없고 모델 안정성 미들웨어만 붙는다.

#### 툴
없음

#### 미들웨어

| 미들웨어 | 설명 |
|---|---|
| `ModelRetryMiddleware` | LLM 응답 실패 시 최대 2회 재시도 (backoff 2.0×, 초기 1 s, 최대 10 s) |
| `PIIMiddleware` (email) | LLM 입력에서 이메일 주소 자동 redact |

---

### 2. `load_context` — 컨텍스트 로딩

반려동물 프로필·기록·스케줄을 조회해 에이전트가 추론할 컨텍스트를 구성한다.  
읽기 전용 툴만 허용되며, 툴 결과에도 PII 검사가 적용된다.

#### 툴

| 툴 이름 | 설명 |
|---|---|
| `get_pet_profile` | pet_id로 반려동물 프로필 조회 |
| `list_recent_records` | pet_id + lookback_days로 최근 기록 목록 조회 |
| `build_care_context` | pet_id + lookback_days로 케어 컨텍스트 빌드 (프로필·기록·스케줄 통합) |
| `list_due_reminders` | pet_id + days_ahead로 예정된 케어 리마인더 목록 조회 |

#### 미들웨어

| 미들웨어 | 설명 |
|---|---|
| `ToolRetryMiddleware` | 4개 컨텍스트 툴 실패 시 최대 1회 재시도 |
| `ToolCallLimitMiddleware` | 노드 실행당 툴 호출 총 6회 제한 |
| `PIIMiddleware` (email) | LLM 입력 및 툴 결과(`apply_to_tool_results=True`)에서 이메일 redact |
| `AgentDebugMiddleware` | 툴 호출 예외를 `ToolMessage`로 정규화해 원본 args 누출 방지 |

---

### 3. `save_records` — 기록 저장

구조화된 레코드를 실제로 DB에 저장한다.  
쓰기 작업이므로 Human-in-the-Loop 승인이 필요하다.

#### 툴

| 툴 이름 | 설명 |
|---|---|
| `save_pet_record` | 구조화된 반려동물 기록 1건 저장 (title, detail, category, status, confidence 포함) |

#### 미들웨어

| 미들웨어 | 설명 |
|---|---|
| `HumanInTheLoopMiddleware` | `save_pet_record` 호출 전 사용자 승인(approve/reject) 요구 |
| `ToolRetryMiddleware` | `save_pet_record` 실패 시 최대 1회 재시도 |
| `ToolCallLimitMiddleware` | `save_pet_record` 호출 5회 제한 |
| `PIIMiddleware` (email) | LLM 입력에서 이메일 redact |
| `AgentDebugMiddleware` | 툴 호출 예외를 `ToolMessage`로 정규화 |

---

## Speech Routes 툴

LangGraph 파이프라인 외부에서 HTTP 라우터(`speech_routes.py`)가 직접 사용하는 툴이다.

| 툴 | 메서드 | 설명 |
|---|---|---|
| `SpeechTools` | `transcribe(audio, content_type)` | 오디오 바이트를 텍스트로 변환 (STT). `SpeechToTextProvider` 위임 |
| `SpeechTools` | `synthesize(text, voice)` | 텍스트를 오디오 바이트로 합성 (TTS). `TextToSpeechProvider` 위임 |

`SpeechTools`는 `AppContext.speech_tools`로 주입되며, 없을 경우 `speech_to_text` / `text_to_speech` 개별 프로바이더로 폴백한다.

---

## 전체 구조 요약

```
LangGraphPetLogAgentPipeline
├── structure_record
│   ├── 툴: 없음
│   └── 미들웨어: ModelRetry, PII(email)
│
├── load_context
│   ├── 툴: get_pet_profile, list_recent_records, build_care_context, list_due_reminders
│   └── 미들웨어: ToolRetry, ToolCallLimit(6회), PII(email+tool_results), AgentDebug
│
└── save_records
    ├── 툴: save_pet_record
    └── 미들웨어: HumanInTheLoop, ToolRetry, ToolCallLimit(5회), PII(email), AgentDebug

SpeechRoutes (HTTP)
└── SpeechTools: transcribe, synthesize
```

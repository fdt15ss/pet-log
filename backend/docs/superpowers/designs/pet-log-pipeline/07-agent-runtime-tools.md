# Agent Runtime, Middleware, Tools

## 역할 구분

```text
application/agents/
  = 누가 무슨 일을 맡는가

agent_runtime/
  = agent를 어떻게 실행하는가

middleware/
  = agent 실행 전후에 끼워 넣는 공통 처리

tools/
  = agent가 호출할 수 있는 행동

infrastructure/
  = 실제 외부 시스템 구현
```

## Agent Runtime

| 파일 | 책임 |
| --- | --- |
| `src/agent_runtime/runtime.py` | LLM 호출 loop와 tool calling 실행기 |
| `src/agent_runtime/prompts.py` | system/developer prompt 조립 |
| `src/agent_runtime/tool_registry.py` | tool 등록, 조회, schema 노출 |
| `src/agent_runtime/memory.py` | 단기 context와 향후 memory hook |

## LangGraph/LangChain 선택

현재 프로젝트의 기본 방향은 LangGraph 우선이다.

판단 근거:

- `PetLogAgentPipeline`은 기록 구조화, 맥락 분석, 위험 감지, 저장, 제안, 리마인더처럼 순서와 상태가 있는 workflow다.
- 보호자 확인, 병원 요약, 알림 후보 생성, 향후 human-in-the-loop가 들어갈 가능성이 높다.
- `agent_runtime/`은 이미 LLM 호출 loop, tool registry, memory, middleware를 분리한 구조라 LangGraph의 graph orchestration과 잘 맞는다.

결정:

- application pipeline과 interface는 LangGraph 또는 LangChain 타입에 의존하지 않는다.
- `src/agent_runtime/` 내부 구현에서만 LangGraph adapter를 둔다.
- LLM provider 호출은 `infrastructure/llm/`의 얇은 provider wrapper로 먼저 구현한다.
- LangChain은 model/tool adapter, provider 통합, prebuilt agent가 명확히 필요한 경우에만 보조적으로 사용한다.
- 단순 rule/mock 구현 단계에서는 LangGraph/LangChain을 추가하지 않는다.

후속 구현 후보:

```text
application pipeline
  -> application agent
  -> AgentRuntimeInterface 후보
  -> LangGraphAgentRuntime
  -> ToolRegistry
  -> infrastructure provider/tool
```

도입 기준:

- agent 실행 중간 상태를 저장하거나 재개해야 한다.
- 보호자 확인 같은 interrupt/resume 흐름이 필요하다.
- 여러 tool 호출과 분기 조건을 graph로 명시해야 한다.
- 실행 경로 추적과 재현 가능한 테스트가 중요해진다.

비도입 기준:

- rule-based policy만으로 충분하다.
- 단일 LLM 호출 후 DTO를 반환하는 단순 provider다.
- application interface skeleton 또는 mock 단계다.

## Middleware

| 파일 | 책임 |
| --- | --- |
| `src/middleware/safety.py` | 위험 질문/금지 응답/병원 상담 안내 guard |
| `src/middleware/logging.py` | 실행 로그 |
| `src/middleware/tracing.py` | agent/tool call 추적 |
| `src/middleware/retry.py` | 안전한 retry 정책 |
| `src/middleware/validation.py` | 입력/출력 schema 검증 |

## Tools

| 파일 | 책임 |
| --- | --- |
| `src/tools/record_tools.py` | 기록 조회, 후보 저장, 기록 ID 조회 |
| `src/tools/profile_tools.py` | 펫 프로필 조회 |
| `src/tools/schedule_tools.py` | 일정/리마인더 조회 |
| `src/tools/care_tools.py` | 케어 답변 보조 기능 |
| `src/tools/speech_tools.py` | STT/TTS tool wrapper |

## Tool 설계 기준

- tool 이름은 안정적이고 명시적으로 둔다.
- 입력은 schema-first로 좁게 정의한다.
- 출력은 deterministic shape으로 둔다.
- 위험 작업은 작은 tool로 분리한다.
- error output에는 원인 힌트, 재시도 조건, 중단 조건을 포함한다.

## Speech Provider

| 파일 | 책임 |
| --- | --- |
| `src/infrastructure/speech/speech_to_text.py` | 음성 입력을 text로 변환하는 STT provider |
| `src/infrastructure/speech/text_to_speech.py` | text 응답을 음성 출력으로 변환하는 TTS provider |

STT/TTS provider는 application layer에서 직접 호출하지 않고 interface 뒤로 숨긴다. 파일 업로드, MIME type, streaming 같은 transport 처리는 `presentation/`에서 처리한다.

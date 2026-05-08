# Pet Log Backend

펫로그 backend는 기록 중심 앱이 아니라, 보호자의 자연어 입력을 구조화하고 누적 맥락을 분석해 행동 제안을 반환하는 AI agent backend를 목표로 한다.

## 먼저 읽을 문서

| 문서 | 용도 |
| --- | --- |
| `docs/superpowers/designs/pet-log-pipeline-interface-design.md` | 설계 문서 인덱스 |
| `docs/superpowers/designs/pet-log-pipeline/10-implementation-guide.md` | 처음 보는 개발자를 위한 구현 위치 안내 |
| `docs/superpowers/plans/2026-05-06-pet-log-agent-sprints.md` | 스프린트 계획 인덱스 |
| `docs/superpowers/plans/pet-log-agent-sprints/` | 스프린트별 작업 카드 |

## 구조 한 줄 요약

```text
presentation -> application pipelines -> application agents -> interfaces -> infrastructure/tools/agent_runtime
```

## 폴더 역할

```text
src/domain/
  순수 도메인 타입. DB, HTTP, LLM SDK import 금지.

src/application/
  제품 흐름과 interface 계약. 외부 구현체에 직접 의존하지 않음.

src/infrastructure/
  실제 구현체 위치. DB, LLM, STT/TTS, rule-based policy, composer 구현.

src/agent_runtime/
  LLM agent 실행 loop, prompt, tool registry, memory.

src/middleware/
  safety, logging, tracing, retry, validation 같은 공통 처리.

src/tools/
  LLM agent가 호출할 수 있는 record/profile/schedule/care/speech tool.

src/presentation/
  CLI, HTTP 같은 외부 진입점. 비즈니스 로직은 두지 않음.

src/composition.py
  concrete 구현체를 pipeline에 주입하는 조립 위치.
```

## 구현 원칙

- 작업은 스프린트 카드 단위로 진행한다.
- 각 카드 완료 전 실패 테스트를 먼저 작성한다.
- `application`과 `domain`에는 DB, FastAPI, OpenAI SDK를 import하지 않는다.
- 실제 동작 구현은 `infrastructure`, `agent_runtime`, `tools`, `presentation` 중 책임에 맞는 곳에 둔다.
- 한 스프린트 완료 후 검증 결과를 확인하고 다음 스프린트로 넘어간다.

## 현재 우선순위

1. `Sprint 1`: in-memory repository와 composition wiring
2. `Sprint 2`: mock record structurer와 core 기록 입력 흐름
3. `Sprint 3`: rule-based 위험 감지, 분석, 제안, 리마인더
4. `Sprint 4`: home feed, care question, pet chat, hospital summary
5. `Sprint 5`: CLI/API entrypoint
6. `Sprint 6`: 실제 DB/LLM/STT/TTS/agent runtime 연결

## 검증 명령

```bash
uv run python -B -m unittest discover -s tests -v
```

```bash
uv run python -B -c "import application.interfaces, agent_runtime, middleware, tools, infrastructure, presentation, composition; print('target imports ok')"
```

```bash
rg -n "fastapi|openai|sqlalchemy|sqlite|postgres|psycopg" src/application src/domain
```

마지막 명령의 기대 결과는 출력 없음이다.

## 실제 LLM smoke test

실제 OpenAI API를 호출하는 수동 확인 스크립트다. `backend/.env`의 `OPENAI_API_KEY`를 읽고, script 내부 smoke fixture helper로 in-memory SQLite seed, repository 조회, provider 조립을 만든 뒤 모델 입력으로 사용한다.

```bash
uv run python -B scripts/smoke_record_summary_provider.py
```

이 명령은 네트워크와 API 비용이 발생할 수 있으므로 자동 테스트에는 포함하지 않는다.

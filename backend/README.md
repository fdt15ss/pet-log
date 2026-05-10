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
uv run python -B -c "import application, agent_runtime, middleware, tools, infrastructure, presentation, composition; print('target imports ok')"
```

```bash
rg -n "fastapi|openai|sqlalchemy|sqlite|postgres|psycopg" src/application src/domain
```

마지막 명령의 기대 결과는 출력 없음이다.

## FastAPI 실행

```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

기본 확인:

```bash
curl http://127.0.0.1:8000/health
```

기록 입력 API:

```text
POST /api/v1/pet-log/records
```

요청 body는 pet profile 전체가 아니라 서버에 저장된 `pet_id`만 받는다.

```json
{
  "pet_id": "pet_01JCM7V8H9Q2K4N6R8T0A1B2C3",
  "text": "오늘 아침 사료를 조금 남겼어",
  "source": "manual",
  "confirm": false
}
```

HTTP 계층은 request/response 변환과 pipeline 호출만 담당한다. FastAPI import는 `src/presentation/http/`와 `main.py`에만 둔다.
DB-backed repository와 pipeline은 `composition.build_app_context()`에서 만들고, FastAPI `lifespan`에서 열고 닫는다.

기록 입력 결과 확인 로그:

```text
record.result | pet_id=... | source=... | mode=preview | confirm=no | candidates=... | saved=... | needs_confirmation=yes | first="meal: 식사" | saved_id=-
```

이 로그는 `presentation.http.pet_log_routes` logger에서 `INFO` 레벨로 남긴다. 미리보기 호출은 `source=ai_preview`, `mode=preview`, `saved=0`, `saved_id=-`이어야 하고, 실제 저장 호출은 저장 성공 시 `mode=saved`, `saved`가 1 이상이어야 한다.

음성 STT API:

```text
POST /api/v1/speech/transcriptions
```

요청은 `multipart/form-data`의 `audio` 파일 필드로 받는다. 서버는 `composition.build_app_context()`에서 연결된 `SpeechToTextProvider`를 통해 Whisper `medium`으로 변환한다.

```bash
curl -F "audio=@recording.webm;type=audio/webm" http://127.0.0.1:8000/api/v1/speech/transcriptions
```

## 로컬 Gemma 3n E4B와 GPT fallback

백엔드 LLM provider는 공통 factory를 통해 OpenAI-compatible chat model interface를 사용한다. `LOCAL_LLM_AUTOSTART=1` 또는 `GEMMA_BASE_URL`이 설정되면 로컬 Gemma 3n E4B endpoint를 primary로 호출하고, `OPENAI_API_KEY`가 있으면 transient failure 시 GPT 모델로 fallback한다.

로컬 예시는 다음 파일에서 시작한다. `GEMMA_MODEL`은 로컬 런타임이 노출하는 실제 모델 이름으로 맞춘다.

```bash
cp .env.example .env
```

vLLM을 코드에서 자동 기동하는 예시:

```env
LLM_EAGER_LOAD=1
LOCAL_LLM_AUTOSTART=1
LOCAL_LLM_RUNTIME=vllm
GEMMA_AUTO_PULL=1
GEMMA_PRELOAD=1
GEMMA_BASE_URL=
GEMMA_MODEL=google/gemma-3n-E4B-it
GEMMA_API_KEY=local-gemma
```

이 설정에서는 백엔드가 실행 시점에 모든 configured LLM provider를 생성하고, 모델 생성 전에 `huggingface-cli download google/gemma-3n-E4B-it`와 `vllm serve google/gemma-3n-E4B-it`를 실행한 뒤 `/v1/chat/completions` ping으로 로컬 모델을 메모리에 올린다. 기본 endpoint는 `http://127.0.0.1:8000/v1`이다. `GEMMA_AUTO_PULL=1`은 대용량 모델 다운로드가 발생할 수 있으므로 자동 다운로드를 원하지 않으면 비워 둔다. 이미 별도 OpenAI-compatible 서버를 켜 둔 경우에는 `LOCAL_LLM_AUTOSTART`를 비우고 `GEMMA_BASE_URL`을 직접 지정한다.

llama.cpp를 사용할 때는 GGUF 모델 정보를 함께 지정한다.

```env
LLM_EAGER_LOAD=1
LOCAL_LLM_AUTOSTART=1
LOCAL_LLM_RUNTIME=llama_cpp
GEMMA_AUTO_PULL=1
GEMMA_PRELOAD=1
GEMMA_BASE_URL=
GEMMA_MODEL=google/gemma-3n-E4B-it
GEMMA_API_KEY=local-gemma
LLAMA_CPP_HF_REPO=ggml-org/gemma-3n-E4B-it-GGUF
LLAMA_CPP_HF_FILE=gemma-3n-E4B-it-Q8_0.gguf
```

llama.cpp 기본 endpoint는 `http://127.0.0.1:8080/v1`이다. 서버는 `llama-server --hf-repo ... --hf-file ... --alias google/gemma-3n-E4B-it` 형태로 시작되어 LangChain 호출부의 모델명은 vLLM과 동일하게 유지된다.

```env
GEMMA_BASE_URL=http://127.0.0.1:1234/v1
GEMMA_MODEL=google/gemma-3n-E4B-it
GEMMA_API_KEY=local-gemma
```

자동 다운로드를 사용하지 않을 때는 모델을 로컬 런타임별 명령으로 미리 준비한다.

```bash
huggingface-cli download google/gemma-3n-E4B-it
huggingface-cli download ggml-org/gemma-3n-E4B-it-GGUF gemma-3n-E4B-it-Q8_0.gguf
```

GPT fallback 예시:

```env
OPENAI_API_KEY=
OPENAI_RECORD_STRUCTURING_MODEL=gpt-5-mini
OPENAI_RECORD_STRUCTURING_FALLBACK_MODEL=gpt-5-nano
OPENAI_RECORD_SUMMARY_MODEL=gpt-5-mini
OPENAI_CARE_ANSWER_MODEL=gpt-5-mini
OPENAI_PET_PERSONA_MODEL=gpt-5-mini
OPENAI_IMAGE_RECORD_UNDERSTANDING_MODEL=gpt-5-mini
```

`OPENAI_*_FALLBACK_MODEL`을 따로 지정하지 않은 provider는 같은 GPT 작업 모델을 fallback으로 사용한다. `.env`는 local secret 파일이므로 git에 커밋하지 않는다. 운영 환경에서는 `.env` 파일 대신 배포 환경변수 또는 secret manager에 같은 키를 등록한다.

## 실제 LLM smoke test

실제 LLM을 호출하는 수동 확인 스크립트다. 로컬에서는 `backend/.env`를 `python-dotenv`로 읽고, 이미 설정된 shell 또는 배포 환경변수는 덮어쓰지 않는다.

자연어 기록 구조화 확인:

```bash
uv run python -B scripts/smoke_record_structurer.py
```

자연어 기록 구조화 후 DB 저장 확인:

```bash
uv run python -B scripts/smoke_record_input_to_db.py
```

기록 요약 provider 확인:

```bash
uv run python -B scripts/smoke_record_summary_provider.py
```

요약 provider smoke script는 script 내부 smoke fixture helper로 in-memory SQLite seed, repository 조회, provider 조립을 만든 뒤 모델 입력으로 사용한다.

이 명령들은 네트워크와 API 비용이 발생할 수 있으므로 자동 테스트에는 포함하지 않는다.

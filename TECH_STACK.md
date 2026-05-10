# Pet Log 기술 스택 발표 자료

이 문서는 `PPT`로 옮기기 쉽도록 슬라이드 단위로 정리한 기술 스택 요약입니다. 각 `## Slide` 섹션은 한 장의 발표 슬라이드로 사용할 수 있습니다.

## Slide 1. 프로젝트 개요

**핵심 메시지:** Pet Log는 반려동물 기록을 저장하는 앱을 넘어, 누적 기록을 해석해 상태 변화와 다음 행동 제안을 제공하는 AI Agent 기반 서비스입니다.

- 프런트엔드: `frontend/app/web`의 Next.js 모바일 우선 웹 앱
- 백엔드: `backend`의 Python AI agent backend
- 주요 기능: 자연어 기록 구조화, 타임라인, 분석, AI 제안, 펫 챗, 음성 STT/TTS
- 개발 방식: 하네스 엔지니어링 기반 기획, UX, AI 사양, 구현 계획, QA 흐름

## Slide 2. 전체 아키텍처

**핵심 메시지:** 화면, API 경계, AI pipeline을 분리해 프런트와 백엔드를 독립적으로 발전시킬 수 있게 구성했습니다.

```text
Browser
  -> Next.js App Router pages
  -> Next.js Route Handler /api/v1/...
  -> FastAPI backend /api/v1/...
  -> application pipeline
  -> LangGraph orchestration
  -> repositories, policies, LLM providers, speech providers, RAG retriever
```

- Next.js Route Handler가 프런트 API 경계와 백엔드 프록시 역할 수행
- FastAPI는 HTTP entrypoint와 pipeline 호출만 담당
- `domain`과 `application` 계층은 DB, HTTP framework, LLM SDK 직접 의존을 피함
- 외부 구현체는 `infrastructure`, `agent_runtime`, `tools`, `presentation`에 배치

## Slide 3. 프런트엔드 스택

**핵심 메시지:** Next.js, React, TypeScript 기반으로 모바일 우선 MVP 화면과 서버 API 경계를 구현했습니다.

| 영역 | 사용 기술 | 역할 |
| --- | --- | --- |
| Framework | Next.js `^16.2.4` | App Router, Route Handler, standalone build |
| UI | React `^19.2.5`, React DOM `^19.2.5` | 페이지와 공통 컴포넌트 |
| Language | TypeScript strict mode | 타입 안정성 |
| Styling | Tailwind CSS, global CSS | 모바일 우선 UI 스타일 |
| HTTP | Axios `^1.15.2` | API 호출과 FastAPI 프록시 |
| Test | `tsx --test` | `src/**/*.test.ts` 단위 테스트 |
| QA | Playwright `^1.59.1` | 모바일 화면 QA와 브라우저 검증 |
| Deploy | Azure App Service, Next.js standalone | Node.js 런타임 배포 |

## Slide 4. 하네스 엔지니어링 기반 프런트 개발

**핵심 메시지:** 프런트엔드 개발은 단순 화면 구현이 아니라, 하네스가 만든 산출물을 기준으로 제품 범위, UX, AI 동작, QA를 순차 검증하는 방식으로 진행했습니다.

- 하네스 기준 문서: `frontend/docs/harness/pet-log-mvp/team-spec.md`
- 방식: Pipeline pattern과 Producer-Reviewer gate
- 산출물 흐름:
  - Product Planner -> MVP scope와 acceptance criteria
  - UX Designer -> 모바일 우선 화면 흐름과 상태 정의
  - AI Agent Designer -> 구조화 입력, 분석, 제안, 안전 경계 정의
  - Orchestrator -> 구현 계획 생성
  - QA Reviewer -> 구현 전 품질 검토
- MVP 기본 범위: 홈 요약, 자연어 기록 입력, 기록 타임라인, 분석 리포트, AI 제안, 펫 프로필

## Slide 5. 백엔드 스택

**핵심 메시지:** Python, FastAPI, LangChain, LangGraph 기반으로 AI agent backend skeleton과 실제 provider 경계를 구성했습니다.

| 영역 | 사용 기술 | 역할 |
| --- | --- | --- |
| Language | Python `>=3.12` | backend package와 agent pipeline 구현 |
| API | FastAPI `>=0.136.1` | HTTP API, health check, 기록 입력, STT API |
| Server | Uvicorn standard `>=0.46.0` | ASGI 개발 및 실행 서버 |
| Agent Graph | LangGraph `>=1.1,<2.0` | 상태 기반 pipeline graph orchestration |
| LLM Adapter | LangChain `>=1.0,<2.0`, LangChain OpenAI `>=1.0,<2.0` | local Gemma 3n E4B, GPT fallback, tool, middleware adapter |
| Storage | SQLite via `sqlite3` | 현재 repository 구현체의 로컬 저장소 |
| Speech | OpenAI Whisper, edge-tts | STT와 TTS provider |
| Test/Lint | `unittest`, Ruff | 백엔드 검증과 정적 분석 |
| Package | `pyproject.toml`, uv, setuptools | Python 의존성 및 패키지 실행 |

## Slide 6. AI와 사용 모델

**핵심 메시지:** 백엔드 LLM은 로컬 Gemma 3n E4B를 primary로 사용하고, 장애나 timeout이 나면 GPT 모델로 fallback할 수 있게 공통 인터페이스를 맞췄습니다.

| 사용 영역 | 모델 또는 provider | 현재 상태 |
| --- | --- | --- |
| 프런트 서버 AI service | `gpt-4o-mini` 기본값, `PET_LOG_OPENAI_MODEL`로 변경 | Next.js Route Handler 내부 OpenAI Responses API 호출 |
| 백엔드 primary LLM | 로컬 Gemma 3n E4B endpoint | `LLM_EAGER_LOAD`, `LOCAL_LLM_AUTOSTART`, `LOCAL_LLM_RUNTIME`, `GEMMA_AUTO_PULL`, `GEMMA_PRELOAD`, `GEMMA_BASE_URL`, `GEMMA_MODEL`, `GEMMA_API_KEY` |
| 기록 구조화 GPT fallback | `gpt-5-mini` 기본값 | `OPENAI_RECORD_STRUCTURING_MODEL` |
| 기록 구조화 fallback | `gpt-5-nano` | `OPENAI_RECORD_STRUCTURING_FALLBACK_MODEL` |
| 기록 요약 GPT fallback | `gpt-5-mini` | `OPENAI_RECORD_SUMMARY_MODEL` |
| 케어 답변 GPT fallback | `gpt-5-mini` | `OPENAI_CARE_ANSWER_MODEL` |
| 펫 페르소나 GPT fallback | `gpt-5-mini` | `OPENAI_PET_PERSONA_MODEL` |
| 이미지 기록 이해 GPT fallback | `gpt-5-mini` | `OPENAI_IMAGE_RECORD_UNDERSTANDING_MODEL` |
| 음성 인식 STT | Whisper `medium` | `WHISPER_MODEL` |
| 음성 합성 TTS | edge-tts `ko-KR-SunHiNeural` | `EDGE_TTS_VOICE` |
| RAG embedding | `text-embedding-3-small` | `OPENAI_CARE_KNOWLEDGE_EMBEDDING_MODEL` 설계 기본값 |
| 개발 하네스 권장 모델 | GPT 5.4 | ECC Codex 모델 권장 기준 |

## Slide 7. LangChain과 LangGraph 적용

**핵심 메시지:** LangGraph는 agent pipeline orchestration에, LangChain은 model, tool, middleware adapter에 사용합니다.

- LangGraph
  - `LangGraphPetLogAgentPipeline`으로 Pet Log pipeline 구성
  - node update streaming과 pipeline contract 테스트 보유
  - 상태 기반 graph orchestration에 적합
- LangChain
  - `ChatOpenAI` 기반 local Gemma 3n E4B primary와 GPT fallback provider 구현
  - `StructuredTool`, `BaseTool` 기반 agent tool registry 구성
  - retry, tracing, safety, validation middleware 구성
- 설계 원칙
  - `domain`과 `application`은 LangChain/LangGraph 타입에 직접 의존하지 않음
  - 실제 framework 의존성은 infrastructure와 agent runtime에 격리
  - `infrastructure.llm.model_factory`가 OpenAI-compatible local endpoint와 OpenAI Responses API 차이를 흡수
  - `LLM_EAGER_LOAD=1`이면 backend startup에서 configured provider를 모두 생성
  - `LOCAL_LLM_AUTOSTART=1`이면 백엔드 코드가 vLLM 또는 llama.cpp 서버를 자동 기동
  - `LOCAL_LLM_RUNTIME=vllm`이면 `vllm serve <GEMMA_MODEL>`와 기본 endpoint `http://127.0.0.1:8000/v1` 사용
  - `LOCAL_LLM_RUNTIME=llama_cpp`이면 `llama-server`와 GGUF 모델을 사용하고 기본 endpoint `http://127.0.0.1:8080/v1` 사용
  - `GEMMA_AUTO_PULL=1`이면 `huggingface-cli download`로 모델을 준비
  - `GEMMA_PRELOAD=1`이면 `/v1/chat/completions` ping으로 로컬 모델을 메모리에 preload

## Slide 8. RAG 설계

**핵심 메시지:** 케어 질문 답변은 반려동물 컨텍스트와 승인된 케어 지식 검색 결과를 함께 사용하는 RAG 구조로 확장할 수 있게 설계했습니다.

```text
Approved care URL
  -> ingestion
  -> text extraction
  -> chunking
  -> embedding
  -> SQLite vector storage
  -> CareKnowledgeRetriever.search()
  -> CareAnswerProvider prompt
  -> sourced care answer
```

- 현재 구현: `CareKnowledgeRetriever` skeleton과 RAG 설계 문서
- 지식 출처: 관리자가 승인한 외부 케어 가이드 URL
- embedding 기본 모델: `text-embedding-3-small`
- 저장소: MVP는 SQLite, 향후 pgvector 또는 외부 vector DB로 교체 가능
- 안전 정책: 진단, 처방, 확정 표현 금지, 위험 증상은 병원 상담 안내 유지
- 확장 작업: URL fetching, SSRF 보호, chunking, embedding persistence, similarity search, citation prompt

## Slide 9. 주요 폴더 구조

**핵심 메시지:** 프런트는 화면과 클라이언트 도메인 로직을 분리하고, 백엔드는 계층형 agent backend 구조를 따릅니다.

```text
frontend/app/web/
├── src/app/          # App Router pages and route handlers
├── src/components/   # app shell, shared UI, map, AI panel
└── src/lib/          # frontend logic, API client, mock store, tests

backend/
├── src/domain/          # pure domain model
├── src/application/     # use case, agent interface, pipeline contract
├── src/infrastructure/  # DB, LLM, STT/TTS, policy, repository
├── src/agent_runtime/   # runtime, prompt, tool registry, memory
├── src/middleware/      # safety, retry, tracing, validation
├── src/tools/           # record, profile, schedule, care, speech tools
└── src/presentation/    # FastAPI HTTP and CLI boundary
```

## Slide 10. 실행과 검증

**핵심 메시지:** 프런트와 백엔드는 각각 독립 실행과 검증이 가능하며, 통합 시 Next.js가 FastAPI로 요청을 프록시합니다.

### 프런트엔드

```bash
cd frontend/app/web
npm install
npm run dev
npm test
npm run lint
npm run typecheck
npm run build
```

### 백엔드

```bash
cd backend
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
uv run python -B -m unittest discover -s tests -v
uv run python -B -c "import application, agent_runtime, middleware, tools, infrastructure, presentation, composition; print('target imports ok')"
rg -n "fastapi|openai|sqlalchemy|sqlite|postgres|psycopg" src/application src/domain
```

마지막 명령은 출력이 없는 상태가 기대값입니다.

## Slide 11. 환경변수

**핵심 메시지:** secret은 코드에 두지 않고 로컬 `.env` 또는 배포 환경변수로 분리합니다.

### 프런트엔드

```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=
PET_LOG_BACKEND_API_BASE_URL=http://127.0.0.1:8000
PET_LOG_BACKEND_PET_ID=pet_01JCM7V8H9Q2K4N6R8T0A1B2C3
PET_LOG_AI_PROVIDER=mock
PET_LOG_OPENAI_MODEL=gpt-4o-mini
PET_LOG_OPENAI_RESPONSES_URL=https://api.openai.com/v1/responses
OPENAI_API_KEY=
```

### 백엔드

```env
OPENAI_API_KEY=
LLM_EAGER_LOAD=1
LOCAL_LLM_AUTOSTART=1
LOCAL_LLM_RUNTIME=vllm
GEMMA_AUTO_PULL=1
GEMMA_PRELOAD=1
GEMMA_BASE_URL=
GEMMA_MODEL=google/gemma-3n-E4B-it
GEMMA_API_KEY=local-gemma
LLAMA_CPP_HF_REPO=ggml-org/gemma-3n-E4B-it-GGUF
LLAMA_CPP_HF_FILE=gemma-3n-E4B-it-Q8_0.gguf
OPENAI_RECORD_STRUCTURING_MODEL=gpt-5-mini
OPENAI_RECORD_STRUCTURING_FALLBACK_MODEL=gpt-5-nano
OPENAI_RECORD_SUMMARY_MODEL=gpt-5-mini
OPENAI_RECORD_SUMMARY_FALLBACK_MODEL=
OPENAI_CARE_ANSWER_MODEL=gpt-5-mini
OPENAI_CARE_ANSWER_FALLBACK_MODEL=
OPENAI_PET_PERSONA_MODEL=gpt-5-mini
OPENAI_PET_PERSONA_FALLBACK_MODEL=
OPENAI_IMAGE_RECORD_UNDERSTANDING_MODEL=gpt-5-mini
OPENAI_IMAGE_RECORD_UNDERSTANDING_FALLBACK_MODEL=
OPENAI_CARE_KNOWLEDGE_EMBEDDING_MODEL=text-embedding-3-small
WHISPER_MODEL=medium
EDGE_TTS_VOICE=ko-KR-SunHiNeural
```

`LLM_EAGER_LOAD=1`이면 backend startup에서 configured LLM provider를 모두 생성합니다. `LOCAL_LLM_AUTOSTART=1`이면 백엔드가 `LOCAL_LLM_RUNTIME`에 따라 `vllm serve` 또는 `llama-server`를 자동 기동합니다. `GEMMA_AUTO_PULL=1`이면 모델 생성 전 `huggingface-cli download`를 실행하고, `GEMMA_PRELOAD=1`이면 `/v1/chat/completions` ping으로 모델을 메모리에 올립니다. `GEMMA_MODEL`은 로컬 LLM 런타임이 OpenAI-compatible endpoint에서 노출하는 실제 모델 이름으로 맞춥니다. `OPENAI_API_KEY`가 있으면 GPT fallback이 활성화됩니다.

## Slide 12. 발표 요약

**핵심 메시지:** Pet Log는 모바일 우선 프런트, 계층형 AI backend, LangGraph agent orchestration, LangChain provider adapter, RAG 확장 설계를 결합한 AI 반려동물 관리 서비스입니다.

- 프런트: Next.js, React, TypeScript, Tailwind, Axios
- 백엔드: Python, FastAPI, LangChain, LangGraph, SQLite
- AI 모델: 로컬 Gemma 3n E4B primary, `gpt-5-mini`/`gpt-5-nano` fallback, `gpt-4o-mini`, Whisper `medium`, `text-embedding-3-small`
- 개발 방식: 하네스 엔지니어링 기반 기획, UX, AI, 구현, QA gate
- 확장성: RAG, speech, image understanding, provider 교체 가능 구조

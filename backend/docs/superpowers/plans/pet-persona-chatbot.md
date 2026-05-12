# 펫 페르소나 챗봇 — 엔드투엔드 구현 계획

## 배경

앱에는 두 가지 채팅 화면이 있다:
1. **AI 챗봇** (왼쪽에서 슬라이드) — 펫 기록 기반 팩트 Q&A. 현재 `sendChatbotMessage` → `/chatbot/messages` 호출 시 HTTP 400 반환
2. **펫 페르소나 채팅** (오른쪽에서 슬라이드) — LLM이 반려동물 _처럼_ 답변. 현재 `createPetReply()` 로컬 함수(키워드 매칭)를 사용하고 백엔드에 전혀 연결되어 있지 않음

백엔드에는 `PetChatPipeline`, `ChatbotRepository`, `pet_chat_routes.py`, `pet_chat_repository.py`가 이미 작성되어 있지만 **연결되지 않은 상태**. 5가지 블로커를 해결해야 파이프라인이 동작한다.

---

## 블로커 (순서대로 수정)

### 1. 도메인 모델 누락
**파일:** `backend/src/domain/models.py`

기존 모델 정의 뒤에 frozen dataclass 2개 추가:

```python
@dataclass(frozen=True)
class ChatbotMessage:
    id: str
    role: str
    content: str
    safety_notice: str | None = None
    referenced_record_ids: tuple[str, ...] = ()
    created_at: str | None = None

@dataclass(frozen=True)
class ChatbotThread:
    id: str
    pet_id: str
    title: str
    updated_at: str
    created_at: str
    messages: tuple[ChatbotMessage, ...] = ()
```

### 2. DB 스키마에 챗봇 테이블 누락
**파일:** `backend/src/infrastructure/database.py`

`initialize_schema()` 내부에 추가:

```sql
CREATE TABLE IF NOT EXISTS chatbot_threads (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    pet_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS chatbot_messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL REFERENCES chatbot_threads(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    safety_notice TEXT,
    referenced_record_ids TEXT NOT NULL DEFAULT '[]',
    provider TEXT,
    model TEXT,
    created_at TEXT NOT NULL
);
```

### 3. SafetyGuard 구체 구현체 없음
**파일:** `backend/src/infrastructure/policies/safety_guard.py`

패스스루 가드 추가 (항상 `None` 반환 — 모든 메시지 통과):

```python
class PassthroughSafetyGuard(SafetyGuard):
    def check(self, text: str) -> SafetyNotice | None:
        return None
```

### 4. AppContext에 챗봇 컴포넌트 미연결
**파일:** `backend/src/composition.py`

상단에 임포트 추가:
```python
from application.agents.care_context import CareContextBuilder
from application.agents.pet_persona import PetPersonaAgent
from application.pipelines.pet_chat import PetChatPipeline
from infrastructure.llm.pet_persona.provider import PetPersonaResponder
from infrastructure.policies.safety_guard import PassthroughSafetyGuard
from infrastructure.repositories.pet_chat_repository import ChatbotRepository
```

`AppContext` 데이터클래스에 필드 추가:
```python
chatbot_repository: ChatbotRepository | None = None
pet_chat_pipeline: PetChatPipeline | None = None
```

`build_app_context()` 내부에 생성 코드 추가:
```python
chatbot_repository = ChatbotRepository(connection=database)
pet_chat_pipeline = PetChatPipeline(
    context_builder=CareContextBuilder(
        pet_profile_reader=pet_profile_reader,
        record_history_reader=record_repository,
        schedule_context_reader=schedule_repository,
    ),
    safety_guard=PassthroughSafetyGuard(),
    pet_persona_agent=PetPersonaAgent(responder=PetPersonaResponder()),
)
```

`return AppContext(...)` 에 추가:
```python
chatbot_repository=chatbot_repository,
pet_chat_pipeline=pet_chat_pipeline,
```

### 5. 챗봇 라우터 미등록
**파일:** `backend/src/presentation/http/routes.py`

임포트 추가:
```python
from presentation.http.pet_chat_routes import build_chatbot_router
```

`build_router()` 내부에 추가:
```python
router.include_router(build_chatbot_router())
```

---

## 프론트엔드: 펫 채팅 패널을 백엔드에 연결

**파일:** `frontend/app/web/src/app/page.tsx`

`sendPetChatMessage` 함수가 로컬 `createPetReply()`를 호출하고 있음. 이를 백엔드 API 호출로 교체.

상태 변경 필요:
- `petChatThreadId: string | null` 상태 추가
- `isPetChatSending: boolean` 상태 추가
- 로컬 `createPetReply()` 함수 제거

새 `sendPetChatMessage` 로직:
1. 유저 메시지 낙관적 추가
2. 로딩 상태 표시 (입력 비활성화)
3. `petChatThreadId`가 없으면 `createChatbotThread(petId, profile.name)` 호출 → thread id 저장
4. `sendChatbotThreadMessage(petChatThreadId, trimmedQuestion)` 호출
5. `result.assistantMessage.content`로 assistant 메시지 추가
6. 에러 시: 알림 표시, 낙관적 메시지 롤백

**API 클라이언트 수정** (`frontend/app/web/src/lib/api-client.ts`):
- `getChatbotThreads`: `pet_id` 파라미터 누락 → 시그니처를 `(petId: string)`으로 변경하고 `params: { pet_id: petId }` 추가
- `createChatbotThread`: `pet_id` 누락 → `petId: string` 파라미터 추가하여 POST body에 포함

---

## 검증 방법

1. 백엔드 기동: `cd backend && uvicorn main:app --reload`
2. `GET /api/v1/chatbot/threads?pet_id=<id>` → 200, `{ ok: true, data: { threads: [] } }`
3. `POST /api/v1/chatbot/threads` with `{ pet_id, title }` → 200, thread 반환
4. `POST /api/v1/chatbot/threads/{id}/messages` with `{ question }` → 200, LLM 답변 반환
5. 프론트엔드 펫 채팅 패널에서 메시지 전송 → LLM이 반려동물 말투로 답변
6. `backend/scripts/smoke_pet_persona.py` 스크립트로 엔드투엔드 검증

---

## 수정 대상 파일 요약

| 파일 | 변경 내용 |
|------|-----------|
| `backend/src/domain/models.py` | `ChatbotMessage`, `ChatbotThread` 추가 |
| `backend/src/infrastructure/database.py` | chatbot 테이블 2개 스키마 추가 |
| `backend/src/infrastructure/policies/safety_guard.py` | `PassthroughSafetyGuard` 추가 |
| `backend/src/composition.py` | `ChatbotRepository` + `PetChatPipeline` 연결 |
| `backend/src/presentation/http/routes.py` | `build_chatbot_router()` 등록 |
| `frontend/app/web/src/app/page.tsx` | `createPetReply()` → 백엔드 API 호출로 교체 |
| `frontend/app/web/src/lib/api-client.ts` | `getChatbotThreads` / `createChatbotThread` 시그니처 수정 |

## 이미 완료 (변경 불필요)

- `backend/src/infrastructure/repositories/pet_chat_repository.py` — 구현 완료
- `backend/src/presentation/http/pet_chat_routes.py` — 구현 완료
- `frontend/app/web/src/lib/types.ts` — `ChatbotThread` / `ChatbotMessage` 타입 존재
- `frontend/app/web/src/lib/api-client.ts` — `sendChatbotThreadMessage` 구현 완료 (백엔드 계약과 일치)

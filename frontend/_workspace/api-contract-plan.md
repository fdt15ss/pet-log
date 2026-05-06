# Pet Log API 연동 계약 계획

## 목적

현재 `app/web`은 `PetLogProvider`에서 mock data와 `localStorage`를 직접 관리합니다. API 연동 1차 작업은 백엔드 구현 전에 계약을 먼저 고정해, 이후 provider를 axios 기반 데이터 경계로 바꿀 수 있게 만드는 것입니다.

이번 문서는 **API 계약과 mock API 구현 기준 문서**입니다. 프론트는 실제 axios HTTP 호출을 사용하고, 1차 서버 응답은 Next.js Route Handler의 메모리 mock store에서 제공합니다. 실제 DB, 인증, 파일 업로드는 후속 스프린트에서 결정합니다. LLM은 서버 provider 경계를 먼저 만들고, 기본 개발 환경에서는 mock 응답을 반환합니다.

## 현재 프론트 저장 경계

- 상태 소유자: `app/web/src/components/pet-log-provider.tsx`
- 저장 키: `pet-log-state-v1`
- 기준 타입: `app/web/src/lib/types.ts`
  - `PetProfile`
  - `RecordEntry`
  - `CareSchedule`
  - `AppSettings`
- 확장 UI 타입: `app/web/src/lib/expansion-state.ts`
  - `ExpansionState`
  - `SharedCareState`
  - `HospitalState`
  - `ShoppingState`
- 현재 생성/수정/삭제 함수
  - `addRecord`
  - `updateRecord`
  - `deleteRecord`
  - `updateProfile`
  - `updateSettings`
  - `addSchedule`
  - `toggleScheduleDone`
  - `deleteSchedule`
  - `updateSharedCareState`
  - `updateHospitalState`
  - `updateShoppingState`

## 공통 응답 형식

API 버전은 `/api/v1`로 시작합니다. 모든 응답은 JSON을 기본으로 합니다.

```ts
type ApiSuccess<T> = {
  ok: true;
  data: T;
};

type ApiFailure = {
  ok: false;
  error: {
    code: string;
    message: string;
  };
};
```

공통 에러 코드는 다음 기준으로 둡니다.

- `VALIDATION_ERROR`: 필수값 누락 또는 타입 불일치
- `NOT_FOUND`: 대상 기록, 일정, 프로필 리소스 없음
- `CONFLICT`: 클라이언트 상태가 서버 최신 상태와 충돌
- `UNAUTHORIZED`: 인증이 필요한 요청에서 사용자 확인 실패
- `INTERNAL_ERROR`: 서버 처리 실패

## 초기 스냅샷

### `GET /api/v1/me/pet-log`

앱 시작 시 필요한 전체 상태를 한 번에 조회합니다.

```ts
type PetLogSnapshot = {
  version: 1;
  profile: PetProfile;
  records: RecordEntry[];
  schedules: CareSchedule[];
  settings: AppSettings;
  readNotificationIds: string[];
  expansionState: ExpansionState;
};
```

응답:

```ts
ApiSuccess<PetLogSnapshot>
```

프론트 전환 기준:

- `PetLogProvider`는 초기 렌더 후 이 API를 호출합니다.
- 호출 전에는 기존 mock data를 표시할 수 있습니다.
- 호출 성공 시 provider 상태를 서버 스냅샷으로 교체합니다.
- 호출 실패 시 기존 `localStorage` 데모 흐름을 유지하고 `syncStatus`를 `offline` 또는 `error`로 표시합니다.

## 프로필 API

### `PUT /api/v1/profile`

반려동물 프로필 전체를 저장합니다.

요청:

```ts
type UpdateProfileRequest = PetProfile;
```

응답:

```ts
ApiSuccess<{ profile: PetProfile }>
```

정책:

- `name`, `breed`는 필수값입니다.
- `notes`는 빈 문자열 제거 후 저장합니다.
- `photoDataUrl`은 계약 1차에서는 문자열로 유지합니다.
- 실제 이미지 파일 업로드와 CDN 저장은 후속 `POST /api/v1/profile/photo` 후보로 분리합니다.

## 기록 API

### `POST /api/v1/ai/records/structure`

저장 전 자연어 기록을 구조화합니다. 프론트는 이 API를 실제 axios 요청으로 호출하고, provider가 mock인지 실제 LLM인지 알지 않습니다.

요청:

```ts
type StructureRecordRequest = {
  detail: string;
  fallbackCategory: RecordCategory;
};
```

응답:

```ts
ApiSuccess<{ structured: StructuredRecord }>
```

서버 책임:

- 원문, 정규화 요약, 추천 분류, 신뢰도, 추출 수치, 확인 필요 여부를 반환합니다.
- 기본 provider는 mock이며 현재 규칙 기반 구조화 계약과 동일한 응답을 반환합니다.
- `PET_LOG_AI_PROVIDER=openai`와 `OPENAI_API_KEY`가 설정되면 서버에서 OpenAI Responses API를 axios로 호출할 수 있습니다.
- LLM 호출 실패, 키 누락, 잘못된 응답 형식은 mock 구조화로 fallback합니다.

### `POST /api/v1/records`

자연어 기록을 생성합니다.

요청:

```ts
type CreateRecordRequest = {
  category: RecordCategory;
  detail: string;
};
```

응답:

```ts
ApiSuccess<{ record: RecordEntry }>
```

서버 책임:

- `id`, `date`, `time`, `title`, `status`를 생성합니다.
- `structured`는 `app/web/src/lib/server/pet-log-ai-service.ts`의 구조화 provider 결과를 저장합니다.
- 프론트는 저장 전 미리보기와 실제 저장 모두 API 경계를 거치므로 나중에 mock provider만 제거할 수 있습니다.

### `PATCH /api/v1/records/:id`

기존 기록의 카테고리와 상세 내용을 수정합니다.

요청:

```ts
type UpdateRecordRequest = {
  category: RecordCategory;
  detail: string;
};
```

응답:

```ts
ApiSuccess<{ record: RecordEntry }>
```

### `DELETE /api/v1/records/:id`

기록을 삭제합니다.

응답:

```ts
ApiSuccess<{ deletedId: string }>
```

프론트 전환 기준:

- 생성과 수정은 서버 구조화 결과를 받은 뒤 화면 상태에 반영합니다.
- API 실패 시 로컬 fallback 기록을 만들거나 이전 `records` 상태를 유지하고 화면에 저장 실패 안내를 표시합니다.
- 삭제는 기존 confirm 흐름을 유지합니다.

## 일정 API

### `POST /api/v1/schedules`

일정을 생성합니다.

요청:

```ts
type CreateScheduleRequest = {
  category: ScheduleCategory;
  title: string;
  dueDate: string;
  repeatLabel: string;
  note: string;
};
```

응답:

```ts
ApiSuccess<{ schedule: CareSchedule }>
```

### `PATCH /api/v1/schedules/:id`

일정 완료 상태 또는 내용을 수정합니다.

요청:

```ts
type UpdateScheduleRequest = Partial<{
  category: ScheduleCategory;
  title: string;
  dueDate: string;
  repeatLabel: string;
  note: string;
  isDone: boolean;
}>;
```

응답:

```ts
ApiSuccess<{ schedule: CareSchedule }>
```

### `DELETE /api/v1/schedules/:id`

일정을 삭제합니다.

응답:

```ts
ApiSuccess<{ deletedId: string }>
```

정책:

- 반복 일정 자동 갱신은 서버 작업 후보로 두되, 1차 API에서는 저장된 `repeatLabel`만 유지합니다.
- 푸시 알림, 시간대 보정, 백그라운드 리마인더는 후속 서버 스프린트에서 다룹니다.

## 설정과 읽음 상태 API

### `PUT /api/v1/settings`

알림 선호와 AI 표시 설정을 저장합니다.

요청:

```ts
type UpdateSettingsRequest = AppSettings;
```

응답:

```ts
ApiSuccess<{ settings: AppSettings }>
```

### `PUT /api/v1/notifications/read`

알림 읽음 상태를 저장합니다.

요청:

```ts
type UpdateReadNotificationsRequest = {
  readNotificationIds: string[];
};
```

응답:

```ts
ApiSuccess<{ readNotificationIds: string[] }>
```

정책:

- 현재 알림은 저장된 기록과 일정으로 프론트에서 계산합니다.
- 실제 푸시 알림과 서버 생성 알림 목록은 후속 작업입니다.

## 확장 UI 상태 API

### `PUT /api/v1/expansion-state`

공동 관리, 병원 연계, 쇼핑 화면의 UI 상태를 저장합니다.

요청:

```ts
type UpdateExpansionStateRequest = Partial<ExpansionState>;
```

응답:

```ts
ApiSuccess<{ expansionState: ExpansionState }>
```

정책:

- 공동 관리의 실제 초대 발송, 권한 검증, 계정 동기화는 후속 서버 작업입니다.
- 병원 연계의 실제 병원 검색, 지도 API, 예약, 리포트 전송은 후속 서버 작업입니다.
- 쇼핑의 상품 피드, 제휴 링크, 결제, 구매 전환 추적은 후속 서버 작업입니다.
- 1차 API는 현재 목업 UI에서 사용자가 고른 상태를 저장하는 데 집중합니다.

## 홈 챗봇 API

### `POST /api/v1/chatbot/messages`

홈 `물어보기` 바텀시트에서 보호자 질문을 전송합니다.

요청:

```ts
type CreateChatbotMessageRequest = {
  question: string;
  contextRecordIds?: string[];
};
```

응답:

```ts
type ChatbotMessageResponse = {
  answer: string;
  referencedRecordIds: string[];
  safetyNotice: string;
  threadId?: string;
};
```

```ts
ApiSuccess<ChatbotMessageResponse>
```

정책:

- 현재 UI는 실제 `/api/v1/chatbot/messages` HTTP 요청을 보내고 서버 AI service 응답을 표시합니다.
- 이 endpoint는 기존 홈 UI 호환용이며, 응답을 서버 mock 대화방에 함께 저장합니다.
- 답변은 진단이 아니라 저장된 기록 기반 참고 안내로 제한합니다.
- 응급, 지속 증상, 상태 악화 가능성이 있는 경우 병원 상담 권장 문구를 포함합니다.

### `GET /api/v1/chatbot/threads`

홈 챗봇의 최근 대화방과 메시지 이력을 조회합니다.

응답:

```ts
type ChatbotThread = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatbotMessage[];
};

type ChatbotMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  referencedRecordIds?: string[];
  safetyNotice?: string;
};
```

```ts
ApiSuccess<{ threads: ChatbotThread[] }>
```

### `POST /api/v1/chatbot/threads`

새 챗봇 대화방을 만듭니다. 제목을 보내지 않으면 `새 질문`을 기본값으로 사용합니다.

### `POST /api/v1/chatbot/threads/:id/messages`

지정한 대화방에 보호자 질문과 AI 답변을 저장합니다.

정책:

- 1차 구현은 Next.js Route Handler의 서버 메모리 mock store에 저장합니다.
- 실제 계정 기반 대화 이력, 장기 보관, 삭제, 검색은 DB/auth 전환 스프린트에서 처리합니다.
- assistant 메시지는 답변 본문과 안전 안내를 분리해 저장합니다.

## 서버 AI Provider 경계

- LLM은 클라이언트에서 직접 실행하지 않고 `app/web/src/lib/server/pet-log-ai-service.ts`에서 실행합니다.
- 기본값은 `PET_LOG_AI_PROVIDER=mock`과 같은 mock provider 동작입니다.
- `PET_LOG_AI_PROVIDER=openai`, `OPENAI_API_KEY`를 설정하면 서버에서 OpenAI Responses API를 호출합니다.
- `PET_LOG_OPENAI_MODEL`로 모델을 지정할 수 있습니다.
- OpenAI provider가 실패하거나 키가 없으면 UI가 깨지지 않도록 mock 답변 또는 mock 구조화로 fallback합니다.
- 프론트 API 계약은 그대로 유지하므로 나중에 Next Route Handler를 별도 백엔드로 옮겨도 챗봇과 기록 구조화 호출 구조는 유지합니다.

## 프론트 전환 순서

1. `app/web` dependencies에 `axios`를 추가합니다.
2. `app/web/src/lib/api-client.ts`를 추가해 `axios.create()` 기반 `apiClient`와 API 함수들을 모읍니다.
   - `baseURL`은 `/api/v1`로 둡니다.
   - 공통 header는 `Content-Type: application/json`을 기본으로 둡니다.
   - axios error는 공통 `ApiFailure` 형식으로 정규화합니다.
3. `PetLogProvider`에 `isLoading`, `error`, `syncStatus`를 추가합니다.
4. 앱 시작 시 `GET /api/v1/me/pet-log`를 호출하고 성공하면 provider 상태를 서버 스냅샷으로 교체합니다.
5. 기록, 프로필, 일정, 설정 mutation을 API 함수 호출로 감쌉니다.
6. 실패 시 로컬 fallback을 적용하거나 이전 상태를 유지하고 사용자에게 저장 실패 메시지를 노출합니다.
7. API가 준비되기 전에는 기존 `localStorage` 저장을 fallback으로 유지합니다.
8. API 전용 모드 전환은 인증, 서버 저장, 마이그레이션 검증 후 별도 스프린트에서 처리합니다.

## Route Handler mock API 구현

- `app/web/src/app/api/v1/[...path]/route.ts`에서 `/api/v1/*` 요청을 받습니다.
- `app/web/src/lib/server/mock-pet-log-store.ts`에 서버 메모리 mock store를 둡니다.
- 프론트는 mock 여부를 알지 않고 `app/web/src/lib/api-client.ts`의 axios 함수만 호출합니다.
- 나중에 실제 서버 저장으로 전환할 때는 Route Handler 내부 store/service 구현만 DB 기반으로 교체하고, 프론트 API client와 provider 호출 구조는 유지합니다.
- mock store는 서버 프로세스 메모리를 사용하므로 dev 서버 재시작 또는 배포 환경 재시작 시 기본 예시 상태로 돌아갈 수 있습니다.

## 검증 기준

- provider의 현재 mutation이 모두 API endpoint 후보와 매핑되어 있어야 합니다.
- `PetProfile`, `RecordEntry`, `CareSchedule`, `AppSettings`, `ExpansionState`가 계약 문서에 포함되어야 합니다.
- 챗봇, 병원 연계, 쇼핑처럼 서버 로직이 필요한 기능은 UI 상태 저장과 실제 외부 연동 범위가 분리되어야 합니다.
- 1차 구현에서는 axios client, Route Handler, mock store만 추가하고 DB 스키마와 인증은 추가하지 않습니다.

## 후속 스프린트 후보

1. Axios API client와 provider 로딩/에러 상태 추가
2. 실제 DB 및 인증 방식 결정
3. Route Handler 내부 mock store를 DB service로 교체
4. 홈 챗봇 실제 답변 생성 및 대화 저장
5. 병원, 쇼핑, 공동 관리 외부 연동 API 분리

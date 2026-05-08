# Record Data Schema

## 목적

이 문서는 사용자가 자연어로 기록을 입력했을 때 데이터가 어떻게 분리되고, DB에는 어떤 형태로 저장되며, 1주일/30일 같은 기간 조회는 어떤 기준으로 가져오는지 정리한다.

## 전체 흐름

```text
사용자 입력 문장
  -> PetLogAgentInput
  -> RecordStructurerInterface
  -> StructuredRecordBatch
     -> StructuredRecordCandidate tuple
  -> PetLogAgentPipeline
  -> RecordRepositoryInterface.save_candidate()
  -> pet_records 여러 row
```

문장 하나에 여러 사건이 섞이면 `StructuredRecordBatch.candidates`에 여러 후보를 담는다. DB에는 batch가 그대로 저장되지 않고, 각 후보가 `pet_records`의 독립 row로 저장된다.

예:

```text
오늘 밥을 조금 먹고 산책은 못 했어
```

구조화 결과:

```text
StructuredRecordBatch
  candidates:
    - title: 식사
      detail: 밥을 조금 먹음
      category: meal
      status: notice
    - title: 산책
      detail: 산책을 하지 못함
      category: walk
      status: notice
```

DB 저장 결과:

```text
pet_records
  row 1: meal / 식사 / 밥을 조금 먹음 / notice
  row 2: walk / 산책 / 산책을 하지 못함 / notice
```

## Domain 구조

저장 전 후보:

```text
StructuredRecordCandidate
  title: str
  detail: str
  category: RecordCategory
  status: RecordStatus
  confidence: float
  needs_confirmation: bool
  measurements: tuple[str, ...]
```

한 입력에서 나온 후보 묶음:

```text
StructuredRecordBatch
  candidates: tuple[StructuredRecordCandidate, ...]
  needs_confirmation: bool
```

`StructuredRecordBatch.needs_confirmation`은 후보 중 하나라도 확인이 필요하면 `True`다. 이 경우 `PetLogAgentPipeline`은 바로 저장하지 않고 확인 단계로 돌린다.

저장된 기록:

```text
PetRecord
  id: str
  pet_id: str
  category: RecordCategory
  title: str
  detail: str
  status: RecordStatus
  recorded_at: str
  source: RecordInputSource
```

## DB 테이블

현재 `pet_records` schema:

```sql
CREATE TABLE IF NOT EXISTS pet_records (
    id TEXT PRIMARY KEY,
    pet_id TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    detail TEXT NOT NULL,
    status TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_pet_records_pet_recorded_at
    ON pet_records (pet_id, recorded_at);
```

현재 저장되는 값:

| 컬럼 | 기준 |
| --- | --- |
| `id` | 저장 시 생성되는 record id |
| `pet_id` | 입력 대상 반려동물 id |
| `category` | 구조화 후보의 category |
| `title` | 구조화 후보의 title |
| `detail` | 구조화 후보의 detail |
| `status` | 구조화 후보의 status |
| `recorded_at` | 저장 시점 UTC ISO timestamp |
| `source` | 현재 저장 경로에서는 `ai_preview` |
| `created_at` | DB row 생성 시점 |
| `updated_at` | DB row 수정 시점 |
| `deleted_at` | soft delete 시점, 기본 `NULL` |

현재 DB에 저장하지 않는 값:

| 값 | 이유 |
| --- | --- |
| `StructuredRecordBatch` 자체 | batch는 저장 단위가 아니라 입력 분리 결과다. |
| `confidence` | 저장 전 구조화 신뢰도이며 현재 record table 컬럼이 없다. |
| `needs_confirmation` | 저장 여부 판단에만 쓰고, 저장된 record에는 남기지 않는다. |
| `measurements` | domain 후보에는 있으나 현재 record table 컬럼이 없다. |
| `original_text` | 현재 record table 컬럼이 없다. |
| `batch_id` | 현재는 한 입력에서 나온 기록끼리 묶는 DB 컬럼이 없다. |

## Enum

```text
RecordCategory
  meal
  walk
  stool
  medical
  behavior

RecordStatus
  normal
  notice
  alert

RecordInputSource
  manual
  voice
  ai_preview
  quick_action
```

## 조회 기준

기본 기록 조회 기준은 `pet_id`다.

```text
RecordRepository.list_recent(pet_id, lookback_days)
RecordRepository.list_by_ids(pet_id, record_ids)
```

현재 `list_recent()` 의도:

```sql
SELECT id, pet_id, category, title, detail, status, recorded_at, source
FROM pet_records
WHERE pet_id = ?
  AND deleted_at IS NULL
ORDER BY recorded_at, created_at;
```

기간 기준 조회는 `recorded_at`을 기준으로 잡는다.

```text
최근 7일
  cutoff = now - 7 days

최근 30일
  cutoff = now - 30 days
```

목표 쿼리:

```sql
SELECT id, pet_id, category, title, detail, status, recorded_at, source
FROM pet_records
WHERE pet_id = ?
  AND deleted_at IS NULL
  AND recorded_at >= ?
ORDER BY recorded_at DESC, created_at DESC;
```

특정 기록 묶음 조회는 `pet_id + record_ids` 기준이다.

```sql
SELECT id, pet_id, category, title, detail, status, recorded_at, source
FROM pet_records
WHERE pet_id = ?
  AND deleted_at IS NULL
  AND id IN (...);
```

반환 순서는 SQL row 순서가 아니라 요청한 `record_ids` 순서를 보존한다.

## 1주일/30일 조회 예시

현재 날짜가 `2026-05-08`이면:

```text
최근 7일 조회
  recorded_at >= 2026-05-01T00:00:00Z

최근 30일 조회
  recorded_at >= 2026-04-08T00:00:00Z
```

사용 예:

```text
list_recent("pet-1", lookback_days=7)
  -> pet-1의 최근 7일 기록

list_recent("pet-1", lookback_days=30)
  -> pet-1의 최근 30일 기록
```

## 현재 주의점

- `list_recent(pet_id, lookback_days)`는 interface에 기간 인자가 있지만, 현재 구현은 아직 날짜 필터를 적용하지 않는다.
- 저장 시 `recorded_at`은 UTC `Z` 포맷으로 생성하지만, seed 데이터에는 timezone 없는 ISO 문자열도 있다.
- 기간 조회를 정확하게 하려면 `recorded_at` 저장 포맷을 UTC ISO로 통일하는 것이 좋다.
- batch 단위 추적이 필요하면 `batch_id`, `original_text`, `confidence`, `measurements` 저장 전략을 별도로 설계해야 한다.

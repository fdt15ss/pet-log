# Hospital Summary Pipeline

## 책임

`HospitalSummaryPipeline`은 병원 제출용 요약을 만든다. 첫 인터페이스 설계에는 포함하되 구현 우선순위는 낮춘다.

```text
HospitalSummaryInput
  -> PetProfileReaderInterface
  -> RecordHistoryReaderInterface
  -> HospitalReportComposerInterface
  -> HospitalSummaryResult
```

## 포함할 정보

- 선택된 기록 목록
- 기록별 날짜/카테고리/상태
- 보호자 입력 원문 또는 요약
- 위험 신호가 있는 경우 safety notice

## 결정

- 병원 제출용 문구는 일반 홈/대화 문구와 분리한다.
- 실제 medical report 포맷은 후속 UX/수의사 검토 이후 확정한다.

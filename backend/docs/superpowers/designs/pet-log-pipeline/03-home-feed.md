# Home Feed Pipeline

## 책임

`HomeFeedPipeline`은 홈 화면에 필요한 today summary, recent changes, alerts, suggestion cards를 조립한다.

```text
HomeFeedInput
  -> PetLogAgentResultReaderInterface
  -> NotificationReaderInterface
  -> ScheduleContextReaderInterface
  -> HomeFeedComposerInterface
  -> HomeFeedResult
```

## 화면에 제공할 정보

- 오늘 요약
- 최근 변화
- 이상 징후
- 행동 제안 카드
- 일정/리마인더

## 결정

- 홈 화면은 core agent 결과를 재해석하지 않는다.
- 홈 화면용 문구와 카드 조립은 `HomeFeedComposerInterface` 뒤에 둔다.
- 알림/일정 소스는 후속 단계에서 repository 또는 notification infrastructure로 구체화한다.

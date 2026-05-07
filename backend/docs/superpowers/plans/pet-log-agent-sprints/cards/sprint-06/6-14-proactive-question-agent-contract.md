# Card 6-14: Proactive question agent contract

**목표:** 홈의 "AI가 먼저 질문하는 한줄 구간"을 application 계약으로 고정한다.

## Files

- Modify: `src/application/dto.py`
- Modify: `src/application/interfaces/agents.py`
- Modify: `src/application/interfaces/policies.py` 또는 provider contract 위치
- Test: `tests/test_proactive_question_agent_contract.py`

## Planning basis

- 홈 오늘 요약
- 최근 변화
- 기록 누락 알림
- AI가 먼저 질문하는 한줄 구간
- AI 질문과 펫 대화의 역할 분리

## Completion criteria

- [ ] `ProactiveQuestionResult` DTO 계약을 만든다.
- [ ] `ProactiveQuestionAgentInterface` 계약을 만든다.
- [ ] 입력은 `PetProfile`, `PetRecord` tuple, `ContextAnalysisResult`, due schedule context를 포함한다.
- [ ] 출력은 question, reason, source record ids, related due items, route를 포함한다.
- [ ] 질문이 필요 없으면 `None`을 반환할 수 있다.
- [ ] 건강 판단이 필요한 질문은 `CareQuestionPipeline` route로 연결한다.
- [ ] 홈에는 최대 1개 질문만 노출한다.

## Verification

```bash
uv run python -B -m unittest tests.test_proactive_question_agent_contract -v
```

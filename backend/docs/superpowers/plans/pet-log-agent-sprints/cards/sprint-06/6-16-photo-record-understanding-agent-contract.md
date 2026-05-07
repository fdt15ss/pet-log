# Card 6-16: Photo record understanding agent contract

**목표:** 사진 첨부 기록과 사진 인식 아이디어를 application 입력 이해 계약으로 고정한다.

## Files

- Modify: `src/application/dto.py` 또는 input DTO 위치
- Modify: `src/application/interfaces/agents.py`
- Modify: `src/application/interfaces/providers.py`
- Add: `src/infrastructure/llm/image_record_understanding_provider.py`
- Test: `tests/test_photo_record_understanding_agent_contract.py`

## Planning basis

- 사진 첨부 기록
- 자는 자세, 사료량, 간식 정보 같은 사진 기반 관찰
- 자동 데이터 구조화
- 낮은 확신 시 입력 수정/보호자 확인

## Completion criteria

- [x] `PhotoRecordUnderstandingAgentInterface` 계약을 만든다.
- [x] `ImageRecordUnderstandingProviderInterface` 계약을 만든다.
- [x] 입력은 `PetProfile`, image bytes, content type, optional user note를 포함한다.
- [x] 출력은 가능한 한 `StructuredRecordCandidate`를 재사용한다.
- [x] 사료량, 배변 상태, 자세처럼 관찰 가능한 정보만 구조화한다.
- [x] 건강 상태를 이미지로 단정하지 않는다.
- [x] 확신이 낮으면 `needs_confirmation=True`로 보호자 확인을 요구한다.

**구현 상태:** `src/infrastructure/agents/photo_record_understanding_agent.py`, `src/infrastructure/llm/image_record_understanding_provider.py`에 class별 스텁을 추가했다. 실제 vision 모델 호출은 아직 구현하지 않는다.

## Verification

```bash
uv run python -B -m unittest tests.test_photo_record_understanding_agent_contract -v
```

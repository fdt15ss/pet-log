# Card 4-7: PetPersonaResponder

**목표:** 펫 말투 mock 응답을 반환한다.

**Files:**
- Modify: `src/infrastructure/llm/pet_persona_responder.py`
- Test: `tests/test_pet_chat_pipeline.py`

**완료 기준:**
- [ ] 일반 메시지에 문자열 응답을 반환한다.
- [ ] pet name 또는 personality를 활용할 수 있다.
- [ ] 건강 판단 질문은 responder가 직접 진단하지 않는다.

**검증 명령:**

```bash
uv run python -B -m unittest tests.test_pet_chat_pipeline -v
```

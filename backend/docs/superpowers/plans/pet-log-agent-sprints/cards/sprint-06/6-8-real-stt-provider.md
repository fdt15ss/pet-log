# Card 6-8: Real STT provider

**목표:** 실제 STT provider를 추가한다.

**Files:**
- Modify: `src/infrastructure/speech/speech_to_text.py`
- Test: `tests/test_speech_provider_contract.py`

**완료 기준:**
- [ ] 실제 provider는 `SpeechToTextInterface`를 충족한다.
- [ ] mock provider와 composition에서 교체 가능하다.
- [ ] provider별 인증/모델 설정은 infrastructure 내부에 둔다.

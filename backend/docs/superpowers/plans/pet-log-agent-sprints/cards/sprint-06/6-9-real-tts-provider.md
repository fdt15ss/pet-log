# Card 6-9: Real TTS provider

**목표:** 실제 TTS provider를 추가한다.

**Files:**
- Modify: `src/infrastructure/speech/text_to_speech.py`
- Test: `tests/test_speech_provider_contract.py`

**완료 기준:**
- [ ] 실제 provider는 `TextToSpeechInterface`를 충족한다.
- [ ] mock provider와 composition에서 교체 가능하다.
- [ ] provider별 voice/model 설정은 infrastructure 내부에 둔다.

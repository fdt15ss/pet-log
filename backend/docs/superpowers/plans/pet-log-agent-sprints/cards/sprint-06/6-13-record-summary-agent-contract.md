# Card 6-13: Record summary agent contract

**목표:** 기획서의 누적 기록 기반 정리 요구를 application 계약으로 고정한다.

**Files:**
- Modify: `src/application/dto.py`
- Modify: `src/application/interfaces/agents.py`
- Modify: `src/application/interfaces/composers.py` 또는 provider 계약 위치
- Test: `tests/test_record_summary_agent_contract.py`

**기획 근거:**
- 문제 행동 요약
- 최근 변화 정리
- 주간/월간 리포트
- 병원 제출용 요약
- 병원 연계의 증상 요약, 변화 기록 정리, 리포트 생성

**완료 기준:**
- [ ] `RecordSummaryResult` DTO 계약을 만든다.
- [ ] `RecordSummaryAgentInterface` 또는 `RecordSummaryComposerInterface` 계약을 만든다.
- [ ] 입력은 `PetProfile`, `PetRecord` tuple, `ContextAnalysisResult`, due schedule context를 포함한다.
- [ ] 출력은 summary text, source record ids, highlights, pattern notes, missing-record notes를 포함한다.
- [ ] 위험 신호는 진단 문장이 아니라 `SafetyNotice` 또는 병원 상담 안내로 분리한다.
- [ ] `HospitalSummaryPipeline`이 후속 단계에서 이 summary 계약을 재사용할 수 있게 경계를 명시한다.

**검증 명령:**

```bash
uv run python -B -m unittest tests.test_record_summary_agent_contract -v
```

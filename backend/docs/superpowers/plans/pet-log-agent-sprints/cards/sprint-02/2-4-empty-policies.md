# Card 2-4: Pipeline 실행용 빈 policy 구현

**목표:** core pipeline이 끝까지 실행될 수 있도록 policy skeleton이 빈 tuple을 반환한다.

**Files:**
- Modify: `src/infrastructure/policies/pattern_analyzer.py`
- Modify: `src/infrastructure/policies/missing_record_policy.py`
- Modify: `src/infrastructure/policies/risk_signal_policy.py`
- Modify: `src/infrastructure/policies/suggestion_composer.py`
- Modify: `src/infrastructure/policies/reminder_planner.py`
- Test: `tests/test_empty_policies.py`

**완료 기준:**
- [ ] `PatternAnalyzer.analyze()`는 빈 tuple을 반환한다.
- [ ] `MissingRecordPolicy.detect_missing_records()`는 빈 tuple을 반환한다.
- [ ] `RiskSignalPolicy.detect_risks()`는 빈 tuple을 반환한다.
- [ ] `SuggestionComposer.compose()`는 빈 tuple을 반환한다.
- [ ] `ReminderPlanner.plan()`은 빈 tuple을 반환한다.

**검증 명령:**

```bash
uv run python -B -m unittest tests.test_empty_policies -v
```

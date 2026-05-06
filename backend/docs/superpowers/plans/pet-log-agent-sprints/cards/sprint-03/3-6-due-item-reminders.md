# Card 3-6: Due item 기반 reminder

**목표:** due item이 있으면 리마인더 후보를 반환한다.

**Files:**
- Modify: `src/infrastructure/policies/reminder_planner.py`
- Test: `tests/test_suggestion_reminder_policies.py`

**완료 기준:**
- [ ] due item이 없으면 빈 tuple을 반환한다.
- [ ] due item이 있으면 그대로 반환한다.
- [ ] records 입력은 이 카드에서 변형하지 않는다.

**검증 명령:**

```bash
uv run python -B -m unittest tests.test_suggestion_reminder_policies -v
```

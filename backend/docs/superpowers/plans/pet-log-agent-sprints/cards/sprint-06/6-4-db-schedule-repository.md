# Card 6-4: Schedule DB repository

**목표:** 실제 DB 기반 schedule repository를 구현한다.

**Files:**
- Modify: `src/infrastructure/repositories/schedule_repository.py`
- Test: `tests/test_database_repositories.py`

**완료 기준:**
- [ ] `list_due_items`가 pet_id와 days_ahead 기준 due item을 반환한다.
- [ ] `PlannedReminder` domain 타입으로 변환한다.

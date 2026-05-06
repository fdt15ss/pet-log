# Card 6-3: Record DB repository

**목표:** 실제 DB 기반 record repository를 구현한다.

**Files:**
- Modify: `src/infrastructure/repositories/record_repository.py`
- Test: `tests/test_database_repositories.py`

**완료 기준:**
- [ ] `list_recent`가 pet_id 기준 기록을 반환한다.
- [ ] `list_by_ids`가 pet_id와 record_ids 기준 기록을 반환한다.
- [ ] `save_candidate`가 후보를 DB row로 저장하고 `PetRecord`를 반환한다.

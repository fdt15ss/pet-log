# Card 6-2: Pet profile DB repository

**목표:** 실제 DB 기반 pet profile repository를 구현한다.

**Files:**
- Modify: `src/infrastructure/repositories/pet_profile_repository.py`
- Test: `tests/test_database_repositories.py`

**완료 기준:**
- [ ] DB row를 `PetProfile`로 변환한다.
- [ ] 없는 pet_id는 명시적 예외를 발생시킨다.
- [ ] application/domain에는 DB client import를 추가하지 않는다.

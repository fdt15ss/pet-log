# Card 5-5: HTTP route skeleton

**목표:** HTTP route skeleton이 pipeline을 호출할 수 있는 구조를 만든다.

**Files:**
- Modify: `src/presentation/http/routes.py`
- Test: `tests/test_http_routes.py`

**완료 기준:**
- [ ] route handler 함수는 request를 변환해 pipeline을 호출한다.
- [ ] route handler 함수는 response dict를 반환한다.
- [ ] FastAPI 도입 여부는 이 카드 시작 전 확정한다.

**검증 명령:**

```bash
uv run python -B -m unittest tests.test_http_routes -v
```

# Card 5-4: HTTP request/response DTO

**목표:** HTTP 계층에서 사용할 request/response 변환 타입을 정의한다.

**Files:**
- Create: `src/presentation/http/routes.py`
- Test: `tests/test_http_routes.py`

**완료 기준:**
- [ ] HTTP request dict를 `PetLogAgentInput`으로 변환한다.
- [ ] `PetLogAgentResult`를 response dict로 변환한다.
- [ ] application/domain에는 HTTP framework import를 추가하지 않는다.

**검증 명령:**

```bash
uv run python -B -m unittest tests.test_http_routes -v
```

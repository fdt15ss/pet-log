# Community Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 프론트 커뮤니티 mock 데이터와 호환되는 백엔드 커뮤니티 API와 SQLite 저장 구조를 만든다.

**Architecture:** 커뮤니티는 core care agent와 분리된 bounded context로 둔다. HTTP route는 request/response 변환만 담당하고, 저장과 필터링은 `CommunityRepository`가 담당한다.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLite, unittest

---

## 파일 구조

- Create: `tests/test_community_repository.py`
- Create: `tests/test_community_http_routes.py`
- Create: `src/infrastructure/repositories/community_repository.py`
- Create: `src/presentation/http/community_routes.py`
- Modify: `src/domain/enums.py`
- Modify: `src/domain/models.py`
- Modify: `src/infrastructure/database.py`
- Modify: `src/infrastructure/repositories/__init__.py`
- Modify: `src/infrastructure/seed_data.py`
- Modify: `src/composition.py`
- Modify: `src/presentation/http/routes.py`
- Modify: `src/presentation/http/schemas.py`
- Modify: `README.md`

### Task 1: Repository Contract

- [ ] **Step 1: Write failing repository tests**

`tests/test_community_repository.py`에 게시글 작성, 피드 필터, 댓글 작성, 반응 등록 테스트를 추가한다.

- [ ] **Step 2: Verify red**

Run: `uv run python -B -m unittest tests.test_community_repository -v`
Expected: import failure for `CommunityRepository`.

- [ ] **Step 3: Implement minimal repository**

도메인 타입, SQLite schema, repository를 추가한다. 피드는 저장 컬럼이 아니라 `created_at`, `distance`, `likes`, `comment_count`로 계산한다.

- [ ] **Step 4: Verify green**

Run: `uv run python -B -m unittest tests.test_community_repository -v`
Expected: OK

### Task 2: HTTP API

- [ ] **Step 1: Write failing HTTP tests**

`tests/test_community_http_routes.py`에 목록, 상세, 게시글 작성, 댓글 작성, 반응 등록 테스트를 추가한다.

- [ ] **Step 2: Verify red**

Run: `uv run python -B -m unittest tests.test_community_http_routes -v`
Expected: route not found or missing context field.

- [ ] **Step 3: Implement route and schemas**

`CommunityPostRequest`, `CommunityCommentRequest`, `CommunityReactionRequest`를 추가하고 router를 `/api/v1/community` 아래에 연결한다.

- [ ] **Step 4: Verify green**

Run: `uv run python -B -m unittest tests.test_community_http_routes -v`
Expected: OK

### Task 3: Composition, Seed, Docs

- [ ] **Step 1: Add seed coverage**

기본 DB 생성 시 커뮤니티 샘플 게시글과 댓글을 함께 넣고 기존 seed 테스트에 최소 검증을 추가한다.

- [ ] **Step 2: Update docs**

`README.md`의 프론트 연동 API 상태와 검증 명령에 커뮤니티 API를 추가한다.

- [ ] **Step 3: Full verification**

Run: `uv run python -B -m unittest discover -s tests -v`
Expected: OK

Run: `uv run python -B -c "import application, agent_runtime, middleware, tools, infrastructure, presentation, composition; print('target imports ok')"`
Expected: `target imports ok`

# 커뮤니티 백엔드 설계

## 목표

프론트 커뮤니티 화면이 사용 중인 게시글, 댓글, 피드 필터 구조를 백엔드 API와 SQLite 저장 구조로 제공한다. 프론트 파일은 수정하지 않고 백엔드 디렉토리 내부 변경만 수행한다.

## 범위

- 게시판: 유기동물, 용품 나눔, 자유게시판, 행동 고민, 후기
- 피드: 인기글, 최신글, 내 주변
- 기능: 게시글 목록, 상세, 작성, 댓글 작성, 반응 등록
- 인기글 기준: `likes + comments` 점수가 10 이상이면 인기글 피드에 포함한다.
- 내 주변 기준: 거리 라벨이 있는 게시글만 포함한다.

## 제외 범위

- 로그인, 권한, 신고, 관리자 기능
- 프론트 코드 변경
- AI 기반 추천
- 위치 좌표 계산

## 구조

- `domain.models`: 커뮤니티 도메인 dataclass를 둔다.
- `infrastructure.database`: community 테이블과 인덱스를 초기화한다.
- `infrastructure.repositories.community_repository`: SQLite와 in-memory 저장소를 모두 지원한다.
- `composition.AppContext`: HTTP route가 사용할 community repository를 보관한다.
- `presentation.http.community_routes`: `/api/v1/community` API를 제공한다.
- `presentation.http.schemas`: request validation과 response 변환을 담당한다.

## API 계약

- `GET /api/v1/community/posts`
  - query: `feed`, `board`
  - response: `{ success: true, data: { posts: [...] } }`
- `GET /api/v1/community/posts/{post_id}`
  - response: `{ success: true, data: { post: {...}, comments: [...] } }`
- `POST /api/v1/community/posts`
  - body: `{ board, title, body, author_name?, distance?, tags? }`
  - response status: `201`
- `POST /api/v1/community/posts/{post_id}/comments`
  - body: `{ body, author_name? }`
  - response status: `201`
- `POST /api/v1/community/posts/{post_id}/reactions`
  - body: `{ reaction_type? }`
  - response: 갱신된 게시글

## 검증

- `uv run python -B -m unittest tests.test_community_repository tests.test_community_http_routes -v`
- `uv run python -B -m unittest discover -s tests -v`
- `uv run python -B -c "import application, agent_runtime, middleware, tools, infrastructure, presentation, composition; print('target imports ok')"`

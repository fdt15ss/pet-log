# Everything Gemini Code Skills Inventory

이 문서는 `/Users/kyungpyokim/everything-claude-code/skills` 경로에 보관된 모든 전문 스킬들을 카테고리별로 정리한 목록입니다. 각 스킬은 `activate_skill(name="스킬이름")`을 통해 활성화하여 상세 가이드와 워크플로우를 확인할 수 있습니다.

---

## 1. AI 및 에이전트 공학 (AI & Agentic Engineering)
에이전트 설계, 자율 루프 구현, 성능 평가 및 비용 관리를 위한 스킬입니다.

- **agent-architecture-audit**: 에이전트 시스템 구조 진단 및 최적화
- **agent-eval**: 에이전트 성능 측정 및 벤치마킹
- **agent-harness-construction**: 에이전트 실행 환경(Harness) 구축
- **agent-introspection-debugging**: 에이전트 내부 상태 분석 및 디버깅
- **agent-payment-x402**: 에이전트 간 결제 및 예산 관리
- **agent-sort**: 필요한 스킬만 골라 에이전트 최적화
- **agentic-engineering**: 에이전트 중심의 소프트웨어 공학 방법론
- **agentic-os**: 에이전트 운영 체제 계층 설계
- **ai-first-engineering**: AI 기반 자동화 우선 개발 방식
- **autonomous-agent-harness**: 완전 자율 에이전트 실행 환경
- **autonomous-loops**: 자율 주행 루프 및 피드백 제어
- **continuous-agent-loop**: 지속적으로 실행되는 에이전트 루프
- **cost-aware-llm-pipeline**: 비용 효율적인 LLM 파이프라인 설계
- **council**: 다중 에이전트 협의 기반 의사결정
- **enterprise-agent-ops**: 기업 규모의 에이전트 운영 및 관리
- **gan-style-harness**: 생성자-평가자(GAN) 방식의 개발 하네스
- **openclaw-persona-forge**: OpenClaw 에이전트 페르소나 설계
- **prompt-optimizer**: 프롬프트 분석 및 품질 개선(Advisory)
- **santa-method**: 다중 에이전트 적대적 검증(Convergence Loop)
- **team-builder**: 병렬 작업을 위한 최적의 에이전트 팀 구성
- **token-budget-advisor**: 답변 깊이와 토큰 사용량 제어 제안

## 2. 개발 프로세스 및 품질 보증 (Process & QA)
기획, 설계, 테스트, 디버깅 및 지속적 학습을 위한 워크플로우입니다.

- **blueprint**: 복잡한 프로젝트를 위한 단계별 실행 계획서
- **architecture-decision-records**: 아키텍처 결정 기록(ADR) 관리
- **product-capability**: 요구사항을 구현 가능한 기능 명세로 변환
- **product-lens**: 제품 관점에서의 기능 검증 및 비판
- **plan-orchestrate**: 다중 단계 계획 수립 및 오케스트레이션
- **tdd-workflow**: 엄격한 테스트 주도 개발 프로세스 강제
- **systematic-debugging**: 체계적인 버그 진단 및 수정
- **verification-loop**: 코드 변경 전후의 완벽한 기능 검증 루프
- **ai-regression-testing**: AI 생성 코드의 회귀 테스트 전략
- **browser-qa**: 브라우저 기반 자동화 테스트 및 QA
- **e2e-testing**: 엔드투엔드 테스트 시나리오 작성 및 실행
- **eval-harness**: 코드/모델 평가용 하네스 구축
- **continuous-learning**: 작업 결과에서 학습하여 지식 축적
- **continuous-learning-v2**: 개선된 학습 시스템 및 본능(Instinct) 추출
- **rules-distill**: 기존 스킬에서 핵심 원칙 추출 및 규칙화
- **skill-comply**: 스킬 준수 여부 자동 시뮬레이션 및 평가
- **skill-stocktake**: 현재 보유한 스킬 자산 인벤토리 관리
- **terminal-ops**: 증거 기반의 터미널 명령어 실행 및 검증

## 3. 프런트엔드 및 UI/UX (Frontend & Design)
웹, 모바일, 디자인 시스템 및 접근성 최적화 스킬입니다.

- **frontend-patterns**: 현대적 프런트엔드 아키텍처 및 상태 관리
- **nextjs-turbopack**: Next.js 및 Turbopack 빌드 최적화
- **angular-developer**: Angular 프레임워크 전문 개발 가이드
- **nuxt4-patterns**: Nuxt 4 프레임워크 개발 패턴
- **vite-patterns**: Vite 기반 프런트엔드 빌드 최적화
- **design-system**: 디자인 시스템 구축 및 코드 동기화
- **motion-ui**: 웹 애니메이션 및 인터랙티브 UI 구현
- **liquid-glass-design**: iOS Liquid Glass 디자인 시스템 구현
- **frontend-slides**: HTML/CSS 기반 웹 프레젠테이션 제작
- **ui-demo**: Playwright를 이용한 고품질 앱 데모 영상 제작
- **ui-to-vue**: UI 디자인을 Vue 컴포넌트로 변환
- **accessibility**: 웹/앱 접근성(WCAG 2.2) 준수 가이드 및 감사
- **ios-icon-gen**: iOS 앱 아이콘 자동 생성
- **swiftui-patterns**: 현대적 SwiftUI 아키텍처 및 상태 관리
- **compose-multiplatform-patterns**: KMP UI 개발 패턴

## 4. 백엔드 및 인프라 (Backend, Ops & Infra)
서버 패턴, 데이터베이스, 컨테이너화 및 배포 전략입니다.

- **backend-patterns**: 백엔드 설계 및 성능 최적화 패턴
- **api-design**: RESTful/GraphQL API 설계 표준
- **hexagonal-architecture**: 헥사고날(Ports & Adapters) 아키텍처
- **fastapi-patterns**: FastAPI 고성능 백엔드 개발 패턴
- **springboot-patterns**: 스프링 부트 레이어드 아키텍처 패턴
- **nestjs-patterns**: NestJS 서버 아키텍처 패턴
- **django-patterns**: Django 웹 프레임워크 베스트 프랙티스
- **laravel-patterns**: Laravel PHP 프레임워크 패턴
- **quarkus-patterns**: Quarkus 자바 프레임워크 패턴
- **postgres-patterns**: PostgreSQL 고급 기능 및 성능 최적화
- **mysql-patterns**: MySQL 성능 최적화 및 스키마 설계
- **redis-patterns**: Redis 데이터 구조 활용 및 성능 최적화
- **clickhouse-io**: ClickHouse OLAP 데이터베이스 활용
- **database-migrations**: 데이터베이스 마이그레이션 안전 자동화
- **docker-patterns**: 효율적인 Docker 이미지 및 컨테이너 관리
- **deployment-patterns**: 현대적 배포 전략(Blue-Green, Canary 등)
- **canary-watch**: 카나리 배포 모니터링 및 롤백 제어
- **bun-runtime**: Bun 런타임 최적화 및 활용
- **flox-environments**: Flox를 이용한 선언적 개발 환경 관리

## 5. 언어별 전문성 (Language Specifics)
언어별 코딩 표준과 특정 기술 문제 해결을 위한 지침입니다.

- **python-patterns / python-testing**: 파이썬 관용구 및 테스트
- **rust-patterns / rust-testing**: 러스트 소유권 및 테스트
- **golang-patterns / golang-testing**: Go 동시성 및 테스트
- **kotlin-patterns / kotlin-testing**: 코틀린 베스트 프랙티스 및 테스트
- **java-coding-standards**: Java 기업용 코딩 표준
- **cpp-coding-standards / cpp-testing**: 현대적 C++ 표준 및 테스트
- **dotnet-patterns / csharp-testing**: .NET 및 C# 개발/테스트
- **perl-patterns / perl-testing / perl-security**: Perl 개발 전반
- **swift-concurrency-6-2 / swift-actor-persistence**: Swift 최신 동시성 및 저장
- **nodejs-keccak256**: Node.js 환경 이더리움 Keccak 해싱 보안
- **coding-standards**: 언어별/프로젝트별 코딩 표준 정의
- **error-handling**: 체계적인 예외 처리 및 복구 전략

## 6. 보안 및 규제 준수 (Security & Compliance)
보안 리뷰, 취약점 탐색 및 산업별 규제 대응 스킬입니다.

- **security-review**: 종합 코드 보안 리뷰 및 체크리스트
- **security-scan**: 설정 파일 및 시크릿 노출 스캔
- **security-bounty-hunter**: 바운티 리포트급 취약점 탐색
- **safety-guard**: 운영 환경의 파괴적 조작 방지 가드레일
- **gateguard**: 코드 배포 전 품질 및 보안 게이트 관리
- **hipaa-compliance**: 미국 의료정보보호법(HIPAA) 준수 가이드
- **healthcare-phi-compliance**: 개인건강정보(PHI) 보호 및 규정 준수
- **defi-amm-security**: DeFi 및 AMM 컨트랙트 보안 진단
- **llm-trading-agent-security**: 자율 트레이딩 에이전트 보안 패턴
- **django-security / laravel-security / springboot-security**: 프레임워크별 보안 설정

## 7. 리서치, 지식 및 미디어 (Research, Knowledge & Media)
심층 분석, 지식 관리 및 멀티미디어 생성 스킬입니다.

- **deep-research**: 심층 웹/코드 리서치 및 보고서 작성
- **exa-search**: Exa AI 검색 엔진 활용 심화 리서치
- **research-ops**: 증거 기반 리서치 워크플로우 운영
- **knowledge-ops**: 지식 베이스 구축, 동기화 및 관리
- **documentation-lookup**: 최신 API 문서 검색 및 요약
- **iterative-retrieval**: 점진적 정보 검색 및 컨텍스트 강화
- **videodb**: 비디오 데이터 분석, 검색 및 액션 자동화
- **video-editing**: AI 지원 비디오 편집 워크플로우
- **remotion-video-creation**: Remotion(React)을 이용한 영상 제작
- **manim-video**: Manim을 활용한 수학적/기술적 애니메이션 제작
- **fal-ai-media**: fal.ai를 활용한 미디어(이미지/영상) 생성
- **article-writing**: 고품질 기술 아티클 및 블로그 작성
- **brand-voice**: 브랜드 고유의 톤앤매너 유지 및 생성
- **content-engine**: 다중 플랫폼 콘텐츠 생성 및 배포 엔진
- **crosspost**: 다중 소셜 플랫폼 동시 포스팅
- **seo**: 기술적 SEO 감사 및 검색 노출 최적화

## 8. 운영 및 비즈니스 (Ops & Business)
프로젝트 관리, 물류, 금융 및 투자자 대응 스킬입니다.

- **github-ops**: GitHub API를 활용한 운영 자동화
- **project-flow-ops**: GitHub/Linear 기반 프로젝트 흐름 관리
- **jira-integration**: Jira 티켓 관리 및 워크플로우 연동
- **google-workspace-ops**: 구글 워크스페이스 운영
- **email-ops**: 이메일 트리아지 및 자동 응답/발송 운영
- **unified-notifications-ops**: 모든 알림 채널 통합 관리 운영
- **finance-billing-ops**: 매출 및 정산 데이터 검증 운영
- **customer-billing-ops**: 고객 빌링 및 구독 관리 운영
- **investor-materials**: 투자자용 자료(IR, Deck) 작성 및 검토
- **investor-outreach**: 투자자 콜드 메일 및 네트워킹 관리
- **market-research**: 시장 조사 및 경쟁사 분석 보고서
- **logistics-exception-management**: 물류 배송 예외 상황 대응 지침
- **inventory-demand-planning**: 재고 및 수요 예측 최적화
- **carrier-relationship-management**: 물류 운송사 관계 및 성과 관리
- **customs-trade-compliance**: 관세 및 무역 규정 준수
- **energy-procurement**: 기업용 에너지 조달 및 비용 최적화

## 9. 워크스페이스 및 기타 (Workspace & Misc)
코드베이스 관리 및 특수 산업 스킬입니다.

- **workspace-surface-audit**: 워크스페이스 내 활용 가능한 리소스 조사
- **codebase-onboarding**: 신규 개발자를 위한 코드베이스 분석 가이드
- **repo-scan**: 코드베이스 자산 분석 및 라이브러리 검출
- **code-tour**: 코드베이스 워크스루 및 가이드 생성
- **ck**: 영구적인 프로젝트 컨텍스트 메모리 관리
- **context-budget**: 컨텍스트 윈도우(토큰) 사용량 관리
- **strategic-compact**: 컨텍스트 보존을 위한 전략적 요약/압축
- **opensource-pipeline**: 비공개 프로젝트 오픈소스화 프로세스
- **healthcare-cdss-patterns / healthcare-emr-patterns**: 의료 도메인 특화
- **scientific-db-pubmed-database / scientific-db-uspto-database**: 과학/특허 데이터 분석
- **visa-doc-translate**: 비자 서류 이미지 번역 및 PDF 생성
- **x-api**: X(트위터) API 연동 및 자동화

---
*Last updated: 2026-05-12*
